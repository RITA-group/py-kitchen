from typing import Optional
import logging
from fastapi import FastAPI, status, HTTPException
import models
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI()


class PaginationContainer(BaseModel):
    """
    TODO: figure out pagination:
    https://firebase.google.com/docs/firestore/query-data/query-cursors
    """
    result: list
    cursor: str = 'not-implemented'


@app.get("/")
def read_root():
    return {"py-kitchen": "test test"}


@app.get("/api/rooms/")
def list_rooms() -> PaginationContainer:
    query = models.Room.collection().stream()
    container = PaginationContainer(
        result=[models.Room.from_snapshot(doc) for doc in query]
    )
    return container


@app.get("/api/rooms/{room_id}")
def get_room(room_id: str) -> models.Room:
    try:
        room = models.Room.from_id(room_id)
    except models.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@app.delete("/api/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: str):
    try:
        room = models.Room.from_id(room_id)
    except models.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    room.delete()
    return


@app.get("/api/rooms/{room_id}/attendees/")
def list_attendees(room_id: str):
    return PaginationContainer(
        result={'test': 'test'},
    )


@app.post("/rooms/{room_id}/attendees/")
def add_attendee(room_id: str):
    return PaginationContainer(
        result={'test': 'test'},
    )


@app.get("/api/profile")
def get_profile():
    return {

    }
