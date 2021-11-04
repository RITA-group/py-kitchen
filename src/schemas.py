from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PaginationContainer(BaseModel):
    """
    TODO: figure out pagination:
    https://firebase.google.com/docs/firestore/query-data/query-cursors
    """
    result: list
    cursor: str = 'not-implemented'


class RoomBase(BaseModel):
    name: str = Field(
        ...,
        example="MSD course"
    )


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: str
    profile_id: str
    created: datetime


class ProfileBase(BaseModel):
    notification_token: Optional[str] = Field(
        ...,
        example="abcD_someletters-numbers:SUPER_long_key_goesHERE"
    )


class Profile(ProfileBase):
    id: str
    display_name: str


class NewAttendee(BaseModel):
    room_id: str = Field(..., example='abcxyz')


class Attendee(BaseModel):
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


class HandToggle(BaseModel):
    hand_up: bool = Field(..., example=True)


class NotificationTokenAdd(BaseModel):
    token: str


class NotificationToken(BaseModel):
    id: str
    profile_id: str
    created: datetime
    message_count: int = 0
    last_message_timestamp: datetime
