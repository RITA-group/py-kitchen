from typing import Optional
import logging
from fastapi import FastAPI, status, HTTPException, Depends, Request
import models
import schemas
from firebase_admin import auth, initialize_app

initialize_app()
logger = logging.getLogger(__name__)
app = FastAPI()


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


test_uid = 'testtesttest'


def test_only_uid(request: Request) -> str:
    return test_uid


def test_user_info(uid: str) -> auth.UserRecord:
    if uid != test_uid:
        raise RuntimeError(
            f'Expected test uid {test_uid} != {uid}'
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


@app.get("/")
def read_root():
    return {"py-kitchen": "test test"}


@app.get("/rooms/")
def list_rooms(
        profile: UserProfile = Depends(UserProfile(test_only_uid)),
) -> schemas.PaginationContainer:
    query = models.DB.rooms.stream()
    rooms = [models.Room.from_snapshot(doc) for doc in query]
    container = schemas.PaginationContainer(
        result=rooms,
    )
    return container


@app.post("/rooms/")
def create_room(
        room_request: schemas.Room,
        profile: models.Profile = Depends(UserProfile(test_only_uid)),
):
    room_ref = models.DB.rooms.document()
    models.Room.save_data(room_ref, room_request.name, profile.id)
    return models.Room.from_snapshot(room_ref.get())


@app.get("/rooms/{room_id}")
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


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    return


#@app.get("/rooms/{room_id}/attendees/")
#def list_attendees(
#        room_id: str,
#        profile: UserProfile = Depends(UserProfile(test_only_uid)),
#):
#    return schemas.PaginationContainer(
#        result={'test': 'test'},
#    )
#
#
#@app.post("/api/rooms/{room_id}/attendees/")
#def add_attendee(
#        room_id: str,
#        profile: UserProfile = Depends(UserProfile(test_only_uid)),
#):
#    return schemas.PaginationContainer(
#        result={'test': 'test'},
#    )


@app.get("/profile")
def get_profile(
        profile: models.Profile = Depends(UserProfile()),
):
    return profile


@app.patch("/profile")
def update_profile(
        profile_request: schemas.Profile,
        profile: models.Profile = Depends(UserProfile()),
):
    ref = models.client.document(f'profiles/{profile.id}')
    ref.update(profile_request.dict())

    return models.Profile.from_snapshot(ref.get())
