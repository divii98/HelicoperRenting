import re

from fastapi import APIRouter, HTTPException, Query

from server.store.bookings import get_availability, get_resource, list_resources

router = APIRouter()
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# "" not "/" - registered under prefix "/api/resources", this must match
# the collection path exactly (no trailing slash). Starlette's default
# redirect_slashes issues a 307 to the "/" version pointing at the
# backend's own absolute URL, which - reached through the Angular dev
# proxy - takes the browser off-origin and fails as an opaque CORS error
# instead of a same-origin request. The frontend calls this path without
# a trailing slash (see resources.service.ts), so the route must too.
@router.get("")
def resources_index():
    return list_resources()


@router.get("/{resource_id}")
def resource_show(resource_id: int):
    resource = get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.get("/{resource_id}/availability")
def resource_availability(resource_id: int, date: str = Query(...)):
    if not _DATE_RE.match(date):
        raise HTTPException(status_code=400, detail="date query param is required (YYYY-MM-DD)")

    availability = get_availability(resource_id, date)
    if availability is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return availability
