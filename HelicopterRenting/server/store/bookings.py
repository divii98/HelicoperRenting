import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from mysql.connector import Error as MySQLError

from server.db.pool import get_connection


class SlotFullError(Exception):
    pass


class InvalidSlotError(Exception):
    pass


def _iso(value) -> Optional[str]:
    """Render a naive (UTC) datetime as an ISO-8601 string with a Z suffix.

    Every datetime this app stores/reads is treated as UTC - see the
    timezone caveat in references/booking-domain.md.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _with_iso_dates(row: dict, *keys: str) -> dict:
    row = dict(row)
    for key in keys:
        if row.get(key) is not None:
            row[key] = _iso(row[key])
    return row


def _parse_time(value) -> tuple[int, int]:
    # mysql-connector-python returns TIME columns as datetime.timedelta,
    # not a string or a time object - this normalizes either shape.
    if isinstance(value, timedelta):
        total_minutes = int(value.total_seconds() // 60)
        return total_minutes // 60, total_minutes % 60
    hours, minutes = str(value).split(":")[:2]
    return int(hours), int(minutes)


def list_resources():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resources WHERE active = 1 ORDER BY id")
        return cursor.fetchall()
    finally:
        conn.close()


def get_resource(resource_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM resources WHERE id = %s AND active = 1", (resource_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()


# Slots are computed on demand from the resource's open/close/slot_minutes
# config rather than pre-materialized as rows - see
# references/booking-domain.md for why (no cron job to generate future
# slots, no table that grows forever). `date_str` ("YYYY-MM-DD") is treated
# as a UTC calendar day. That's a deliberate MVP simplification: fine for a
# single-timezone deployment, but see references/booking-domain.md before
# using this across timezones.
def _build_slots_for_day(resource: dict, date_str: str) -> list[tuple[datetime, datetime]]:
    year, month, day = (int(part) for part in date_str.split("-"))
    open_hour, open_min = _parse_time(resource["open_time"])
    close_hour, close_min = _parse_time(resource["close_time"])

    day_start = datetime(year, month, day, open_hour, open_min, tzinfo=timezone.utc)
    day_end = datetime(year, month, day, close_hour, close_min, tzinfo=timezone.utc)

    slots = []
    cursor = day_start
    step = timedelta(minutes=resource["slot_minutes"])
    while cursor < day_end:
        slot_end = cursor + step
        if slot_end > day_end:
            break
        slots.append((cursor, slot_end))
        cursor = slot_end
    return slots


def get_availability(resource_id: int, date_str: str):
    resource = get_resource(resource_id)
    if not resource:
        return None

    slots = _build_slots_for_day(resource, date_str)
    if not slots:
        return {"resource": resource, "slots": []}

    day_start, _unused = slots[0]
    _unused, day_end = slots[-1]

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT slot_start, COUNT(*) AS booked
            FROM bookings
            WHERE resource_id = %s AND status = 'confirmed'
              AND slot_start >= %s AND slot_start < %s
            GROUP BY slot_start
            """,
            (resource_id, day_start.replace(tzinfo=None), day_end.replace(tzinfo=None)),
        )
        booked_by_slot = {row["slot_start"]: row["booked"] for row in cursor.fetchall()}
    finally:
        conn.close()

    out_slots = []
    for slot_start, slot_end in slots:
        booked = booked_by_slot.get(slot_start.replace(tzinfo=None), 0)
        out_slots.append(
            {
                "slotStart": _iso(slot_start),
                "slotEnd": _iso(slot_end),
                "capacity": resource["capacity"],
                "booked": booked,
                "available": max(0, resource["capacity"] - booked),
            }
        )

    return {"resource": resource, "slots": out_slots}


def _parse_slot_start(slot_start_iso: str) -> datetime:
    try:
        value = datetime.fromisoformat(slot_start_iso.replace("Z", "+00:00"))
    except ValueError as err:
        raise InvalidSlotError("Invalid slot") from err
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _lock_name(resource_id: int, slot_start: datetime) -> str:
    key = f"booking:{resource_id}:{slot_start.isoformat()}"
    # MySQL's GET_LOCK() lock names are capped at 64 characters, so the key
    # is hashed down to fit - the same tradeoff Postgres's hashtext()
    # accepts in the parent skill (a theoretical hash collision is fine;
    # the generated-column unique index below is the actual correctness
    # guarantee either way).
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


# Concurrency-safe booking creation. Two requests for the same resource +
# slot ALWAYS race in production (two people tap "book" within the same
# second) - a naive "check availability, then insert" is not safe, because
# both requests can pass the check before either commits.
#
# MySQL has no transaction-scoped advisory lock like Postgres's
# pg_advisory_xact_lock. GET_LOCK()/RELEASE_LOCK() are the closest
# equivalent, but they are *connection*-scoped, not transaction-scoped: the
# lock is NOT released automatically on COMMIT/ROLLBACK, only by an
# explicit RELEASE_LOCK() on the same connection (or when that connection
# closes). That's why this function keeps a single pooled connection for
# the lock, the transaction, and the release - see
# references/booking-domain.md for the full explanation and what happens
# if you get this wrong.
def create_booking(
    *, resource_id: int, user_id: str, slot_start_iso: str, notes: Optional[str]
) -> dict:
    resource = get_resource(resource_id)
    if not resource:
        raise InvalidSlotError("Resource not found")

    slot_start = _parse_slot_start(slot_start_iso)
    date_str = slot_start.strftime("%Y-%m-%d")
    matched = next(
        (s for s in _build_slots_for_day(resource, date_str) if s[0] == slot_start), None
    )
    if not matched:
        raise InvalidSlotError("Slot does not align with resource availability")
    if slot_start < datetime.now(timezone.utc):
        raise InvalidSlotError("Slot is in the past")
    _matched_start, slot_end = matched

    slot_start_naive = slot_start.replace(tzinfo=None)
    slot_end_naive = slot_end.replace(tzinfo=None)
    lock_name = _lock_name(resource_id, slot_start)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    booking = None
    try:
        cursor.execute("SELECT GET_LOCK(%s, 10) AS acquired", (lock_name,))
        if cursor.fetchone()["acquired"] != 1:
            raise SlotFullError("This slot is busy, please try again")

        try:
            conn.start_transaction()

            cursor.execute(
                """
                SELECT unit_number FROM bookings
                WHERE resource_id = %s AND slot_start = %s AND status = 'confirmed'
                """,
                (resource_id, slot_start_naive),
            )
            taken_units = {row["unit_number"] for row in cursor.fetchall()}

            unit_number = next(
                (unit for unit in range(1, resource["capacity"] + 1) if unit not in taken_units),
                None,
            )
            if unit_number is None:
                raise SlotFullError("This slot is fully booked")

            cursor.execute(
                """
                INSERT INTO bookings
                  (resource_id, user_id, unit_number, slot_start, slot_end, status, notes)
                VALUES (%s, %s, %s, %s, %s, 'confirmed', %s)
                """,
                (resource_id, user_id, unit_number, slot_start_naive, slot_end_naive, notes),
            )
            booking_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
            booking = _with_iso_dates(cursor.fetchone(), "slot_start", "slot_end", "created_at")
        except MySQLError as err:
            conn.rollback()
            # 1062 = duplicate entry - the generated-column unique index
            # (bookings_resource_slot_unit_unique) caught a double-booking
            # the lock somehow let through. This is the last-resort safety
            # net; see references/booking-domain.md. Never remove that
            # index as an "optimization".
            if err.errno == 1062:
                raise SlotFullError("This slot is fully booked") from err
            raise
        except SlotFullError:
            conn.rollback()
            raise
    finally:
        # RELEASE_LOCK() is a SELECT, so mysql-connector-python leaves an
        # "unread result" on the cursor until it's fetched - closing the
        # cursor without fetching raises InternalError("Unread result
        # found") and masks whatever actually happened in the try block.
        cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
        cursor.fetchone()
        cursor.close()
        conn.close()

    return booking


def get_bookings_for_user(user_id: str) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT b.*, r.name AS resource_name
            FROM bookings b
            JOIN resources r ON r.id = b.resource_id
            WHERE b.user_id = %s
            ORDER BY b.slot_start DESC
            """,
            (user_id,),
        )
        return [
            _with_iso_dates(row, "slot_start", "slot_end", "created_at")
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


# Ownership-scoped on purpose - bookings.id is a small sequential integer,
# so an unauthenticated/unscoped lookup would let anyone enumerate other
# people's bookings just by guessing ids.
def get_booking_for_user(booking_id: int, user_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT b.*, r.name AS resource_name
            FROM bookings b
            JOIN resources r ON r.id = b.resource_id
            WHERE b.id = %s AND b.user_id = %s
            """,
            (booking_id, user_id),
        )
        row = cursor.fetchone()
        return _with_iso_dates(row, "slot_start", "slot_end", "created_at") if row else None
    finally:
        conn.close()


def cancel_booking(booking_id: int, user_id: str) -> Optional[dict]:
    # MySQL has no `RETURNING` clause (unlike Postgres) - UPDATE then a
    # separate SELECT is the substitute, checking `cursor.rowcount` to know
    # whether the UPDATE actually matched a row.
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'cancelled'
            WHERE id = %s AND user_id = %s AND status = 'confirmed'
              AND slot_start > UTC_TIMESTAMP()
            """,
            (booking_id, user_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None

        cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        row = cursor.fetchone()
        return _with_iso_dates(row, "slot_start", "slot_end", "created_at")
    finally:
        conn.close()
