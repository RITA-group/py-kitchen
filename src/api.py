import logging
from typing import Optional
from datetime import datetime
from fastapi.routing import APIRouter
from fastapi import status, HTTPException, Depends, Path, Body, Query
from fastapi.responses import Response

import dependencies as deps
import models, schemas, crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/rooms/")
def list_rooms(
        profile: models.Profile = Depends(deps.UserProfile(test=True)),
        db=Depends(deps.get_db)
):
    container = schemas.PaginationContainer(
        result=crud.list_rooms(db),
    )
    return container


@router.post(
    "/rooms/",
    response_model=models.Room,
)
def create_room(
        room: schemas.RoomCreate,
        db=Depends(deps.get_db),
        profile: models.Profile = Depends(deps.UserProfile(test=True)),
):
    return crud.create_room(db, room, profile)


@router.get(
    "/rooms/{room_id}",
    response_model=models.Room,
)
def get_room(
        room_id: str,
        db=Depends(deps.get_db),
        profile: models.Profile = Depends(deps.UserProfile(test=True)),
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
        profile: models.Profile = Depends(deps.UserProfile(test=True)),
):
    try:
        room = crud.get_room(db, room_id)
    except crud.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    if room.owner_id != profile.id:
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
        profile: models.Profile = Depends(deps.UserProfile(test=True)),
):
    query = models.attendees
    if room_id:
        query = query.where(
            'room_id', '==', models.client.document(f'rooms/{room_id}')
        )
    query = query.order_by(
        'created',
        direction=models.firestore.Query.DESCENDING
    ).limit(limit)

    return schemas.PaginationContainer(
        result=[models.Attendee.from_snapshot(doc) for doc in query.stream()],
    )


@router.post(
    "/attendees/",
    response_model=models.Attendee,
)
def add_attendee(
        data: schemas.NewAttendee,
        profile: models.Profile = Depends(deps.UserProfile('test')),
):
    # check the room
    room = models.client.document(f'rooms/{data.room_id}').get()
    if not room.exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with {data.room_id} id doesn't exist."
        )

    # check if already added
    if list(models.attendees.where(
                'profile_id', '==', profile.id
            ).where(
                'room_id', '==', data.room_id
            ).stream()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile with {profile.id} id already joined {data.room_id} room."
        )
    # create new one
    new_attendee = models.attendees.document()
    new_attendee.set(
        {
            'name': profile.display_name,
            'profile_id': models.client.document(f'profiles/{profile.id}'),
            'room_id': models.client.document(f'rooms/{data.room_id}'),
            'created': datetime.now(),
            'hand_up': False,
            'answers': 0,
            'room_owner_likes': 0,
            'peer_likes': 0
        }
    )

    return models.Attendee.from_snapshot(new_attendee.get())


@router.delete("/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        profile: models.Profile = Depends(deps.UserProfile('test')),
):
    ref = models.attendees.document(attendee_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    if models.Attendee.from_snapshot(snapshot).profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee_id} doesn't belong to current user."
        )
    ref.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/attendees/{attendee_id}",
    response_model=models.Attendee,
)
def get_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        profile: models.Profile = Depends(deps.UserProfile('test')),
):
    snapshot = models.client.document(f'attendees/{attendee_id}').get()
    if not snapshot.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )

    attendee = models.Attendee.from_snapshot(snapshot)
    if attendee.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee_id} doesn't belong to current user."
        )

    return attendee


@router.put(
    "/attendees/{attendee_id}/hand",
    response_model=schemas.HandToggle,
)
def hand_toggle(
        attendee_id: str = Path(..., title="Attendee id"),
        data: schemas.HandToggle = Body(
            ...,
            title="True if the attendee raises her hand.",
        ),
        profile: models.Profile = Depends(deps.UserProfile('test')),
):
    ref = models.client.document(f'attendees/{attendee_id}')
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    if models.Attendee.from_snapshot(snapshot).profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee_id} doesn't belong to current user."
        )
    ref.update(
        {
            'hand_up': data.hand_up,
            'hand_change_timestamp': datetime.now(),
        }
    )

    return schemas.HandToggle(
        hand_up=models.Attendee.from_snapshot(ref.get()).hand_up
    )


@router.get("/profile")
def get_profile(
        profile: models.Profile = Depends(deps.UserProfile()),
):
    return profile


@router.patch("/profile")
def update_profile(
        profile_request: schemas.Profile,
        profile: models.Profile = Depends(deps.UserProfile()),
):
    ref = models.client.document(f'profiles/{profile.id}')
    ref.update(profile_request.dict())

    return models.Profile.from_snapshot(ref.get())
