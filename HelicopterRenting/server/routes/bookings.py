from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.auth.dependencies import require_user
from server.store.bookings import (
    InvalidSlotError,
    SlotFullError,
    cancel_booking,
    create_booking,
    get_booking_for_user,
    get_bookings_for_user,
)

router = APIRouter()


class CreateBookingBody(BaseModel):
    resourceId: int
    slotStart: str
    notes: Optional[str] = None


# "" not "/" - same trailing-slash pitfall as resources.py's index route;
# the frontend posts to this path without a trailing slash.
@router.post("", status_code=201)
def bookings_create(body: CreateBookingBody, user=Depends(require_user)):
    try:
        return create_booking(
            resource_id=body.resourceId,
            user_id=user["id"],
            slot_start_iso=body.slotStart,
            notes=body.notes,
        )
    except SlotFullError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    except InvalidSlotError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


# NOTE: `/mine` must be registered before `/{booking_id}` below. FastAPI
# (via Starlette) matches routes in registration order, and a request for
# `/mine` would otherwise hit the `/{booking_id}: int` route first and fail
# int conversion (422) instead of falling through - the same route-order
# pitfall as Express, see references/architecture.md.
@router.get("/mine")
def bookings_mine(user=Depends(require_user)):
    return get_bookings_for_user(user["id"])


# Scoped to the caller's own bookings (see store/bookings.py) - a session
# is required even to view a single booking by id.
@router.get("/{booking_id}")
def bookings_show(booking_id: int, user=Depends(require_user)):
    booking = get_booking_for_user(booking_id, user["id"])
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.patch("/{booking_id}/cancel")
def bookings_cancel(booking_id: int, user=Depends(require_user)):
    cancelled = cancel_booking(booking_id, user["id"])
    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail="Booking not found, not yours, or no longer cancellable",
        )
    return cancelled
