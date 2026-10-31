# The bookable catalog, defined in code and upserted into the `resources`
# table on every server start (see db/migrate.py). This is the first file
# to edit for a new domain - replace these placeholder rows with real
# resources (courts, doctors, rooms, rental units, ...).
#
# Field guide:
#   capacity     - how many simultaneous bookings one slot can hold.
#                  1 = exclusive (a court, a room, a doctor's slot).
#                  N = shared (a fitness class with 12 spots, N rental units).
#   slotMinutes  - length of one bookable slot for this resource.
#   openTime / closeTime - daily booking window, 24h "HH:MM", same every day
#                  in this starter (see references/booking-domain.md to add
#                  per-weekday hours or blackout dates).
#   priceCents   - 0 for free bookings; otherwise price per slot in cents.
RESOURCES = [
    {
        "id": 1,
        "name": "Robinson R44 — Skyline City Tour",
        "description": (
            "A 30-minute loop over the downtown skyline and waterfront in a "
            "nimble 3-seat Robinson R44. Great first helicopter flight."
        ),
        "category": "city",
        "capacity": 3,
        "slotMinutes": 30,
        "openTime": "08:00",
        "closeTime": "18:00",
        "priceCents": 24900,
        "active": True,
    },
    {
        "id": 2,
        "name": "Bell 407 — Mountain Peaks Adventure",
        "description": (
            "A 45-minute charter over ridgelines and alpine lakes in a "
            "spacious 4-seat Bell 407, with a wide-view doors-on cabin."
        ),
        "category": "mountain",
        "capacity": 4,
        "slotMinutes": 45,
        "openTime": "07:00",
        "closeTime": "17:00",
        "priceCents": 39900,
        "active": True,
    },
    {
        "id": 3,
        "name": "Airbus AS350 — Sunset Coastal Flight",
        "description": (
            "A 30-minute evening flight tracing the coastline as the sun "
            "sets, in a 5-seat Airbus AS350 with panoramic windows."
        ),
        "category": "coastal",
        "capacity": 5,
        "slotMinutes": 30,
        "openTime": "15:00",
        "closeTime": "20:00",
        "priceCents": 34900,
        "active": True,
    },
]
