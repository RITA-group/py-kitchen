from pydantic import BaseModel, Field
from typing import Optional
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
    owner_id: str
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


class HandToggle(BaseModel):
    hand_up: bool = Field(..., example=True)
