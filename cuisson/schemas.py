from pydantic import BaseModel, Field
from typing import Optional


class PaginationContainer(BaseModel):
    """
    TODO: figure out pagination:
    https://firebase.google.com/docs/firestore/query-data/query-cursors
    """
    result: list
    cursor: str = 'not-implemented'


class Room(BaseModel):
    name: str = Field(..., example="MSD course")


class Profile(BaseModel):
    notification_token: Optional[str] = Field(..., example="abcD_someletters-numbers:SUPER_long_key_goesHERE")
