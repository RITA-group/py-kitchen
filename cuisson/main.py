import logging
from typing import Optional
from uvicorn import Config, Server
from datetime import datetime
from fastapi.routing import APIRouter
from fastapi import FastAPI, status, HTTPException, Depends, Request, Path, Body, Query
from fastapi.responses import Response
from firebase_admin import auth, initialize_app
import models, schemas, settings

initialize_app()
logger = logging.getLogger(__name__)

app_router = APIRouter()

app = FastAPI(
    title='RITA API',
    description=settings.description,
    version=settings.version,
    openapi_url=settings.prefix + '/openapi.json',
    docs_url=settings.prefix + '/',
    redoc_url=settings.prefix + '/redoc',
)


@app.middleware('http')
async def header_settings(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = 'no-store'
    return response


def uid_from_authorization_token(request: Request) -> str:
    header = request.headers.get("Authorization", None)

    if not header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not provided."
        )

    token = header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authentication error {repr(e)}"
        )
    return decoded_token['uid']


def test_only_uid(request: Request) -> str:
    return settings.test_uid


def test_user_info(uid: str) -> auth.UserRecord:
    if uid != settings.test_uid:
        raise RuntimeError(
            f'Expected test uid {settings.test_uid} != {uid}'
        )

    return auth.UserRecord({
        'localId': uid,
        'displayName': 'Test Testovich',
        'email': 'donotemailme@test.com',
        #'phoneNumber': '11111111',
    })


class UserProfile:
    def __init__(self, fetch_uid: Optional[callable] = None):
        if fetch_uid:
            self.fetch_uid = fetch_uid
            self.fetch_user = test_user_info
        else:
            self.fetch_uid = uid_from_authorization_token
            self.fetch_user = auth.get_user

    def __call__(self, request: Request) -> models.Profile:
        uid = self.fetch_uid(request)
        # get or create profile
        user_info = self.fetch_user(uid)

        ref = models.DB.profiles.document(uid)
        snapshot = ref.get()
        if not snapshot.exists:
            models.Profile.save_data(ref, user_info.display_name)
            snapshot = ref.get()

        return models.Profile.from_snapshot(snapshot)


@app_router.get("/health")
def health_check():
    return {"status": "ok"}


@app_router.get("/rooms/")
def list_rooms(
        profile: UserProfile = Depends(UserProfile(test_only_uid)),
):
    query = models.client.collection('rooms').stream()
    rooms = [models.Room.from_snapshot(doc) for doc in query]
    container = schemas.PaginationContainer(
        result=rooms,
    )
    return container


@app_router.post("/rooms/")
def create_room(
        room_request: schemas.Room,
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
):
    room_ref = models.client.collection('rooms')
    room = room_ref.document()
    room.set({
        'name': room_request.name,
        'owner_id': models.client.document(f'profiles/{profile.id}'),
        'created': datetime.now(),
    })
    return models.Room.from_snapshot(room.get())


@app_router.get(
    "/rooms/{room_id}",
    response_model=models.Room,
)
def get_room(
        room_id: str,
        profile: UserProfile = Depends(UserProfile(test_only_uid)),
):
    try:
        room = models.Room.from_id('rooms', room_id)
    except models.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@app_router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
        room_id: str,
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
):
    try:
        room = models.Room.from_id('rooms', room_id)
    except models.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    if room.owner_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Room {room_id} doesn't belong to current user."
        )
    models.DB.rooms.document(room_id).delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app_router.get(
    "/attendees/",
    response_model=schemas.PaginationContainer,
)
def list_attendees(
        profile: UserProfile = Depends(UserProfile(test_only_uid)),
        limit: int = Query(50, title='Number of results per request'),
        room_id: Optional[str] = Query(None, title='Room id'),
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


@app_router.post(
    "/attendees/",
    response_model=models.Attendee,
)
def add_attendee(
        data: schemas.NewAttendee,
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
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


@app_router.delete("/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
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


@app_router.get(
    "/attendees/{attendee_id}",
    response_model=models.Attendee,
)
def get_attendee(
        attendee_id: str = Path(..., title="Attendee id"),
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
):
    attendee = models.client.document(f'attendees/{attendee_id}').get()
    if not attendee.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee with {attendee_id} id doesn't exist."
        )
    if attendee.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Attendee {attendee_id} doesn't belong to current user."
        )

    return models.Attendee.from_snapshot(attendee)


@app_router.put(
    "/attendees/{attendee_id}/hand",
    response_model=schemas.HandToggle,
)
def hand_toggle(
        attendee_id: str = Path(..., title="Attendee id"),
        data: schemas.HandToggle = Body(
            ...,
            title="True if the attendee raises her hand.",
        ),
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
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


@app_router.get("/profile")
def get_profile(
        profile: models.Profile = Depends(UserProfile()),
):
    return profile


@app_router.patch("/profile")
def update_profile(
        profile_request: schemas.Profile,
        profile: models.Profile = Depends(UserProfile()),
):
    ref = models.client.document(f'profiles/{profile.id}')
    ref.update(profile_request.dict())

    return models.Profile.from_snapshot(ref.get())


app.include_router(
    app_router,
    prefix=settings.prefix,
)


if __name__ == '__main__':

    server = Server(
        Config(
            app,
            host="localhost",
            port=8080,
            log_level='debug',
        ),
    )
    server.run()
