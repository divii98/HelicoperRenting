from server.data.resources import RESOURCES
from server.db.pool import get_connection


def _index_exists(cursor, table: str, index_name: str) -> bool:
    # MySQL has no `CREATE INDEX IF NOT EXISTS` (unlike Postgres) - this is
    # the workaround so ensure_schema() stays idempotent across every boot.
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s
        """,
        (table, index_name),
    )
    return cursor.fetchone()[0] > 0


def _ensure_index(cursor, table: str, index_name: str, ddl: str) -> None:
    if not _index_exists(cursor, table, index_name):
        cursor.execute(ddl)


def ensure_schema() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # `id` is a plain INT PRIMARY KEY (not AUTO_INCREMENT) on purpose -
        # resources are a code-defined catalog, upserted by fixed id on
        # every boot. Direct DB edits to a resource row will be overwritten
        # on next restart; edit data/resources.py instead. If you later add
        # an admin UI for resources, switch this to AUTO_INCREMENT and drop
        # the upsert loop below.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
              id INT PRIMARY KEY,
              name VARCHAR(255) NOT NULL,
              description TEXT NOT NULL,
              category VARCHAR(100) NOT NULL,
              capacity INT NOT NULL DEFAULT 1,
              slot_minutes INT NOT NULL DEFAULT 60,
              open_time TIME NOT NULL DEFAULT '09:00:00',
              close_time TIME NOT NULL DEFAULT '21:00:00',
              price_cents INT NOT NULL DEFAULT 0,
              active TINYINT(1) NOT NULL DEFAULT 1
            ) ENGINE=InnoDB
            """
        )

        # Self-rolled email/password auth (see references/architecture.md
        # for why this template doesn't pull in a Better-Auth-style
        # library): a `users` table and a server-side `sessions` table,
        # the session token living in an httponly cookie.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id CHAR(36) PRIMARY KEY,
              name VARCHAR(255) NOT NULL,
              email VARCHAR(255) NOT NULL UNIQUE,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
              id CHAR(36) PRIMARY KEY,
              user_id CHAR(36) NOT NULL,
              token CHAR(64) NOT NULL UNIQUE,
              expires_at TIMESTAMP NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT sessions_user_fk FOREIGN KEY (user_id)
                REFERENCES users (id) ON DELETE CASCADE
            ) ENGINE=InnoDB
            """
        )
        _ensure_index(
            cursor,
            "sessions",
            "sessions_user_id_idx",
            "CREATE INDEX sessions_user_id_idx ON sessions (user_id)",
        )

        # `bookings.id` is AUTO_INCREMENT - unlike resources, bookings are
        # created dynamically by users at request time, not upserted from
        # code. `confirmed_slot_key` is a generated column that is NULL
        # unless status = 'confirmed'; the unique index on it is MySQL's
        # substitute for a Postgres partial unique index (MySQL has no
        # `UNIQUE ... WHERE` syntax) - see references/booking-domain.md.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
              id INT AUTO_INCREMENT PRIMARY KEY,
              resource_id INT NOT NULL,
              user_id CHAR(36) NOT NULL,
              unit_number INT NOT NULL,
              slot_start DATETIME NOT NULL,
              slot_end DATETIME NOT NULL,
              status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
              notes TEXT,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              confirmed_slot_key VARCHAR(160) GENERATED ALWAYS AS (
                IF(status = 'confirmed',
                   CONCAT(resource_id, ':', unit_number, ':', slot_start),
                   NULL)
              ) STORED,
              CONSTRAINT bookings_resource_fk FOREIGN KEY (resource_id)
                REFERENCES resources (id),
              CONSTRAINT bookings_user_fk FOREIGN KEY (user_id)
                REFERENCES users (id)
            ) ENGINE=InnoDB
            """
        )
        _ensure_index(
            cursor,
            "bookings",
            "bookings_resource_slot_unit_unique",
            "CREATE UNIQUE INDEX bookings_resource_slot_unit_unique "
            "ON bookings (confirmed_slot_key)",
        )
        _ensure_index(
            cursor,
            "bookings",
            "bookings_user_idx",
            "CREATE INDEX bookings_user_idx ON bookings (user_id)",
        )

        for resource in RESOURCES:
            cursor.execute(
                """
                INSERT INTO resources
                  (id, name, description, category, capacity, slot_minutes,
                   open_time, close_time, price_cents, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  name = VALUES(name),
                  description = VALUES(description),
                  category = VALUES(category),
                  capacity = VALUES(capacity),
                  slot_minutes = VALUES(slot_minutes),
                  open_time = VALUES(open_time),
                  close_time = VALUES(close_time),
                  price_cents = VALUES(price_cents),
                  active = VALUES(active)
                """,
                (
                    resource["id"],
                    resource["name"],
                    resource["description"],
                    resource["category"],
                    resource["capacity"],
                    resource["slotMinutes"],
                    resource["openTime"],
                    resource["closeTime"],
                    resource["priceCents"],
                    resource.get("active", True),
                ),
            )

        conn.commit()
    finally:
        conn.close()
