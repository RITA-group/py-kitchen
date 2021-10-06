from typing import Optional
import logging
from fastapi import FastAPI, status, HTTPException
import model
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


@app.get("/rooms/")
def list_rooms() -> PaginationContainer:
    query = model.Room.collection().stream()
    container = PaginationContainer(
        result=[model.Room.from_snapshot(doc) for doc in query]
    )
    return container


@app.get("/rooms/{room_id}")
def get_room(room_id: str) -> model.Room:
    try:
        room = model.Room.from_id(room_id)
    except model.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    return room


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: str):
    try:
        room = model.Room.from_id(room_id)
    except model.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with {room_id} id doesn't exist."
        )
    room.delete()
    return
