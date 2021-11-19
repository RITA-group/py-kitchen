import logging
from typing import Optional
from fastapi.routing import APIRouter
from fastapi import status, HTTPException, Depends, Path, Query
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

import authorization
import schemas
import firestore
import messaging
import services
import realtime_db
import utils

from utils import raise_forbidden

logger = logging.getLogger(__name__)

router = APIRouter()


def fetch_attendee(
    attendee_id: str = Path(..., title="Attendee id"),
    crud: firestore.Crud = Depends(),
) -> schemas.Attendee:
    try:
        attendee = crud.get_attendee(attendee_id)
    except firestore.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    return attendee


def fetch_room(
    room_id: str = Path(..., title="Room id"),
    crud: firestore.Crud = Depends(),
) -> schemas.Room:
    try:
        room = crud.get_room(room_id)
    except firestore.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get(
    "/rooms",
    response_model=schemas.PaginationContainer,
)
def list_rooms(
    relation: Optional[firestore.RoomRelationTypes] = Query(
        None,
        title='Filter based on profile relation to the room',
    ),
    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
):
    if relation == firestore.RoomRelationTypes.created:
        rooms = crud.list_rooms(auth.profile)
    elif relation == firestore.RoomRelationTypes.joined:
        attendees = crud.list_attendees(
            limit=100, profile_id=auth.profile.id
        )
        rooms = crud.fetch_rooms([a.room_id for a in attendees])
    else:
        rooms = crud.list_rooms()

    container = schemas.PaginationContainer(
        result=rooms,
    )
    return container


@router.post(
    "/rooms",
    response_model=schemas.Room,
)
def create_room(
    room: schemas.RoomCreate,

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
    realtime: realtime_db.Crud = Depends(),
):
    new_room = crud.create_room(room, auth.profile)
    realtime.set_room(new_room)
    return new_room


@router.get(
    "/rooms/{room_id}",
    response_model=schemas.Room,
)
def get_room(
    room: schemas.Room = Depends(fetch_room),

    auth: authorization.Auth = Depends(),
):
    return room


@router.get(
    "/realtime_room_format/{room_id}",
    response_model=schemas.RealtimeRoom,
)
def realtime_room_format(
    auth: authorization.Auth = Depends(),
    room: schemas.Room = Depends(fetch_room),
    realtime: realtime_db.Crud = Depends(),
):
    return realtime.get_room(room)


@router.post(
    "/realtime_room_update/{room_id}",
    response_model=schemas.RealtimeRoom,
)
def realtime_room_set(
    auth: authorization.Auth = Depends(),
    room: schemas.Room = Depends(fetch_room),
    realtime: realtime_db.Crud = Depends(),
):
    return realtime.set_room(room)


@router.get(
    "/rooms/{room_id}/next_attendee",
    response_model=Optional[schemas.Attendee],
)
def next_attendee(
    attendee_id: Optional[str] = Query(
        None,
        title='Force a specific attendee.'
    ),
    room: schemas.Room = Depends(fetch_room),
    order: firestore.OrderTypes = Query(
        firestore.OrderTypes.least_answers,
        title='Algorithm used to pick the next attendee.'
    ),

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
    realtime: realtime_db.Crud = Depends(),
    picker: firestore.NextAttendee = Depends(),
):
    # Only owner can call next attendee
    if room.profile_id != auth.profile.id:
        raise_forbidden(f"Room {room.id} doesn't belong to current user.")

    if order == firestore.OrderTypes.specific_attendee and not attendee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"If {firestore.OrderTypes.specific_attendee} is selected, "
                   f"attendee_id must be provided."
        )

    if attendee_id:
        # make sure attendee exists
        attendee = fetch_attendee(attendee_id, crud)
        # Validate the attendee belongs to the room it's assigned
        if attendee.room_id != room.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendee with {attendee_id} is not in the room."
            )
        # Assume the specific attendee is needed since id was provided
        picker.order = firestore.OrderTypes.specific_attendee

    next_in_queue = picker.next_attendee()
    # even if there is no next attendee we stop all previous answers
    crud.stop_all_answers(room.id)
    # TODO: optimize this
    realtime.set_answering(room, next_in_queue)
    realtime.set_room_queue(room)
    if not next_in_queue:
        return None

    crud.start_answer(next_in_queue.id)
    realtime.set_answering(room, next_in_queue)
    realtime.set_room_queue(room)
    return crud.get_attendee(next_in_queue.id)


@router.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
    auth: authorization.Auth = Depends(),
    room: schemas.Room = Depends(fetch_room),
    crud: firestore.Crud = Depends(),
    realtime: realtime_db.Crud = Depends(),
):
    if room.profile_id != auth.profile.id:
        raise_forbidden(f"Room {room.id} doesn't belong to current user.")

    room_id = room.id
    crud.delete_room(room.id)
    realtime.delete_room(room_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/attendees",
    response_model=schemas.PaginationContainer,
)
def list_attendees(
    room_id: Optional[str] = Query(None, title='Room id'),
    limit: int = Query(50, title='Number of results per request'),

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
):
    attendees = crud.list_attendees(limit, room_id)

    return schemas.PaginationContainer(
        result=attendees,
    )


@router.post(
    "/attendees",
    response_model=schemas.Attendee,
)
def create_attendee(
    data: schemas.NewAttendee,

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
    realtime: realtime_db.Crud = Depends(),
):
    # check the room
    room = fetch_room(data.room_id, crud)

    # check if already added
    if crud.list_attendees(
        limit=1, room_id=room.id, profile_id=auth.profile.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile with {auth.profile.id} id already joined {room.id} room."
        )
    new_attendee = crud.create_attendee(room.id, auth.profile)
    realtime.set_room_attendees(room)

    return new_attendee


@router.delete("/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendee(
    auth: authorization.Auth = Depends(),
    attendee: schemas.Attendee = Depends(fetch_attendee),
    crud: firestore.Crud = Depends(),
    realtime: realtime_db.Crud = Depends(),
):
    if attendee.profile_id != auth.profile.id:
        raise_forbidden(f"Attendee {attendee.id} doesn't belong to current user.")

    try:
        room = crud.get_room(attendee.room_id)
    except firestore.NotFound:
        pass
    else:
        realtime.set_room_attendees(room)

    crud.delete_attendee(attendee.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/attendees/{attendee_id}",
    response_model=schemas.Attendee,
)
def get_attendee(
    auth: authorization.Auth = Depends(),
    attendee: schemas.Attendee = Depends(fetch_attendee),
) -> schemas.Attendee:
    return attendee


@router.put(
    "/attendees/{attendee_id}/hand_toggle",
    response_model=schemas.Attendee,
)
def hand_toggle(
    auth: authorization.Auth = Depends(),
    attendee: schemas.Attendee = Depends(fetch_attendee),
    crud: firestore.Crud = Depends(),
    message: messaging.Message = Depends(),
    realtime: realtime_db.Crud = Depends(),
):
    if attendee.profile_id != auth.profile.id:
        raise_forbidden(f"Attendee {attendee.id} doesn't belong to current user.")
    room = fetch_room(attendee.room_id, crud)
    updated_attendee = crud.hand_toggle(attendee)
    realtime.set_room_queue(room)
    message.maybe_notify_instructor(updated_attendee)

    return updated_attendee


@router.get(
    "/profile",
    response_model=schemas.Profile,
)
def get_profile(
    auth: authorization.Auth = Depends(),
):
    return auth.profile


@router.get(
    "/profile/notification_tokens",
    response_model=schemas.PaginationContainer,
)
def list_notification_tokens(
    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
):
    return schemas.PaginationContainer(
        result=crud.list_notification_tokens(auth.profile.id)
    )


@router.post(
    "/profile/notification_tokens",
    response_model=schemas.NotificationToken,
)
def create_notification_token(
    data: schemas.NotificationTokenAdd,

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
):
    try:
        token = crud.get_notification_token(data.token)
    except firestore.NotFound:
        pass
    else:
        if token.profile_id != auth.profile.id:
            raise_forbidden(f"Token doesn't belong to current user.")

        return token

    token = crud.create_notification_token(auth.profile, data.token)
    return token


@router.delete(
    "/profile/notification_tokens/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification_token(
    token: str = Path(..., title="Notification token string"),

    auth: authorization.Auth = Depends(),
    crud: firestore.Crud = Depends(),
):
    try:
        token = crud.get_notification_token(token)
    except firestore.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{token} doesn't exist."
        )

    if token.profile_id != auth.profile.id:
        raise_forbidden(f"Token doesn't belong to current user.")

    crud.delete_notification_token(token.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/token",
)
def test_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth=Depends(services.auth_transport),
):
    if not form_data.username.endswith('@t.org'):
        raise HTTPException(
            status_code=400,
            detail=f"{form_data.username} is not registered as api test account.",
        )

    try:
        user = auth.get_user_by_email(form_data.username)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Test login error: {repr(e)}",
        )

    custom_token = auth.create_custom_token(user.uid)
    user_token = utils.get_user_token_from(custom_token)['idToken']

    return {"access_token": user_token, "token_type": "bearer"}
