from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot


class PaginationContainer(BaseModel):
    """
    TODO: figure out pagination:
    https://firebase.google.com/docs/firestore/query-data/query-cursors
    """
    result: list
    cursor: str = 'not-implemented'


class FirebaseModel(BaseModel):
    @classmethod
    def from_snapshot(cls, doc: DocumentSnapshot):
        data = {'id': doc.id}
        for key, value in doc.to_dict().items():
            if hasattr(value, 'id'):
                value = value.id
            data[key] = value
        return cls(**data)


class RoomBase(FirebaseModel):
    name: str = Field(
        ...,
        min_length=3,
        example="MSD course",
    )


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: str
    profile_id: str
    created: datetime


class ProfileBase(FirebaseModel):
    notification_token: Optional[str] = Field(
        ...,
        example="abcD_someletters-numbers:SUPER_long_key_goesHERE"
    )


class Profile(ProfileBase):
    id: str
    display_name: str


class NewAttendee(FirebaseModel):
    room_id: str = Field(..., example='abcxyz')


class Attendee(FirebaseModel):
    id: str
    name: str
    profile_id: str
    room_id: str
    created: datetime
    # Active fields
    hand_up: bool = False
    answering: bool = False
    hand_change_timestamp: Optional[datetime] = None
    answers: int = 0
    room_owner_likes: int = 0
    peer_likes: int = 0


class HandToggle(FirebaseModel):
    hand_up: bool = Field(..., example=True)


class NotificationTokenAdd(FirebaseModel):
    token: str


class NotificationToken(FirebaseModel):
    id: str
    profile_id: str
    created: datetime
    message_count: int = 0
    last_message_timestamp: Optional[datetime]


class RealtimeRoom(BaseModel):
    profile_id: str
    attendees: Optional[list[Attendee]] = None
    queue: Optional[list[Attendee]] = None
    answering: Optional[Attendee] = None
