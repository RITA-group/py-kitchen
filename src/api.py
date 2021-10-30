import logging
from typing import Optional
from fastapi.routing import APIRouter
from fastapi import status, HTTPException, Depends, Path, Query
from fastapi.responses import Response

import dependencies as deps
import schemas
import crud

logger = logging.getLogger(__name__)

router = APIRouter()


def fetch_attendee(attendee_id: str, db) -> schemas.Attendee:
    try:
        attendee = crud.get_attendee(db, attendee_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    return attendee


def fetch_room(room_id: str, db) -> schemas.Room:
    try:
        room = crud.get_room(db, room_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/rooms/")
def list_rooms(
        profile: schemas.Profile = Depends(deps.profile),
        db=Depends(deps.get_db)
):
    container = schemas.PaginationContainer(
        result=crud.list_rooms(db),
    )
    return container


@router.post(
    "/rooms/",
    response_model=schemas.Room,
)
def create_room(
        room: schemas.RoomCreate,
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    return crud.create_room(db, room, profile)


@router.get(
    "/rooms/{room_id}",
    response_model=schemas.Room,
)
def get_room(
        room_id: str = Path(..., title="Room id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    return fetch_room(room_id, db)


@router.get(
    "/rooms/{room_id}/next_attendee",
    response_model=Optional[schemas.Attendee],
)
def next_attendee(
    room_id: str = Path(..., title="Room id"),
    attendee_id: Optional[str] = Query(
        None,
        title='Force a specific attendee.'
    ),
    order: crud.OrderTypes = Query(
        crud.OrderTypes.least_answers,
        title='Algorithm used to pick the next attendee.'
    ),
    db=Depends(deps.get_db),
    profile: schemas.Profile = Depends(deps.profile),
):
    # Only owner can call next attendee
    room = fetch_room(room_id, db)
    if room.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Room {room_id} doesn't belong to current user."
        )

    if order == crud.OrderTypes.specific_attendee and not attendee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"If {crud.OrderTypes.specific_attendee} is selected, "
                   f"attendee_id must be provided."
        )

    if attendee_id:
        # make sure attendee exists
        attendee = fetch_attendee(attendee_id, db)
        # Validate the attendee belongs to the room it's assigned
        if attendee.room_id != room.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendee with {attendee_id} is not in the room."
            )
        # Assume the specific attendee is needed since id was provided
        order = crud.OrderTypes.specific_attendee
        picker = crud.NextAttendee(db, room_id, attendee)
    else:
        picker = crud.NextAttendee(db, room_id)

    try:
        attendee = picker(order)
    except crud.NotFound:
        return None
    finally:
        # even if there is no next attendee we stop all previous answers
        crud.stop_all_answers(db, room.id)

    crud.start_answer(db, attendee.id)
    return crud.get_attendee(db, attendee.id)


@router.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
        room_id: str = Path(..., title="Room id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    try:
        room = crud.get_room(db, room_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    if room.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Room {room_id} doesn't belong to current user."
        )
    crud.delete_room(db, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/attendees/",
    response_model=schemas.PaginationContainer,
)
def list_attendees(
        room_id: Optional[str] = Query(None, title='Room id'),
        limit: int = Query(50, title='Number of results per request'),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    attendees = crud.list_attendees(db, limit, room_id)

    return schemas.PaginationContainer(
        result=attendees,
    )


@router.post(
    "/attendees/",
    response_model=schemas.Attendee,
)
def create_attendee(
        data: schemas.NewAttendee,
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    # check the room
    try:
        crud.get_room(db, data.room_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with {data.room_id} id doesn't exist."
        )

    # check if already added
    if crud.list_attendees(
      db, limit=1, room_id=data.room_id, profile_id=profile.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile with {profile.id} id already joined {data.room_id} room."
        )

    return crud.create_attendee(db, data.room_id, profile)


@router.delete("/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    try:
        attendee = crud.get_attendee(db, attendee_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    if attendee.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee.id} doesn't belong to current user."
        )
    crud.delete_attendee(db, attendee.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/attendees/{attendee_id}",
    response_model=schemas.Attendee,
)
def get_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
) -> schemas.Attendee:
    return fetch_attendee(attendee_id, db)


@router.put(
    "/attendees/{attendee_id}/hand_toggle",
    response_model=schemas.Attendee,
)
def hand_toggle(
        attendee_id: str = Path(..., title="Attendee id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.profile),
):
    attendee = crud.get_attendee(db, attendee_id)
    if attendee.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee.id} doesn't belong to current user."
        )

    return crud.hand_toggle(db, attendee)


@router.get(
    "/profile",
    response_model=schemas.Profile,
)
def get_profile(
        profile: schemas.Profile = Depends(deps.profile),
):
    return profile
