import logging
from typing import Optional
from fastapi.routing import APIRouter
from fastapi import status, HTTPException, Depends, Path, Query
from fastapi.responses import Response

import dependencies as deps
import schemas, crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/rooms/")
def list_rooms(
        profile: schemas.Profile = Depends(deps.test_profile),
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
        profile: schemas.Profile = Depends(deps.test_profile),
):
    return crud.create_room(db, room, profile)


@router.get(
    "/rooms/{room_id}",
    response_model=schemas.Room,
)
def get_room(
        room_id: str,
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.test_profile),
):
    try:
        room = crud.get_room(db, room_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@router.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
        room_id: str,
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.test_profile),
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
        profile: schemas.Profile = Depends(deps.test_profile),
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
        profile: schemas.Profile = Depends(deps.test_profile),
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
        profile: schemas.Profile = Depends(deps.test_profile),
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
        profile: schemas.Profile = Depends(deps.test_profile),
) -> schemas.Attendee:
    try:
        attendee = crud.get_attendee(db, attendee_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    return attendee


@router.put(
    "/attendees/{attendee_id}/hand_toggle",
    response_model=schemas.Attendee,
)
def hand_toggle(
        attendee_id: str = Path(..., title="Attendee id"),
        db=Depends(deps.get_db),
        profile: schemas.Profile = Depends(deps.test_profile),
):
    attendee = crud.get_attendee(db, attendee_id)
    if attendee.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee.id} doesn't belong to current user."
        )
    # TODO: Change state

    return attendee


@router.get(
    "/profile",
    response_model=schemas.Profile,
)
def get_profile(
        profile: schemas.Profile = Depends(deps.profile),
):
    return profile


@router.get(
    "/user",
)
def get_profile(
    current_user=Depends(deps.user)
):
    return 'test'
