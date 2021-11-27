from fastapi import Depends
from typing import Optional
from json import loads
from firebase_admin import db as realtime_db

import firestore
import schemas
import services


class Crud:
    realtime: realtime_db
    db_crud: firestore.Crud

    def __init__(
        self,
        db_crud: firestore.Crud = Depends(),
        realtime: realtime_db = Depends(services.realtime_db_transport),
    ):
        self.db_crud = db_crud
        self.realtime = realtime

    def _get_attendees(self, room_id: str):
        return self.db_crud.list_attendees(
            limit=200, room_id=room_id, descending=False,
        )

    def _get_in_queue(self, room_id):
        return self.db_crud.attendees_in_queue(
            limit=200, room_id=room_id,
        )

    @staticmethod
    def _to_dict(model: schemas.BaseModel) -> dict:
        """
        Schema models know how to convert to json special fields.
        Convert to json and back from it so we can pass data to the client
        which is not aware of special data fields.
        """
        return loads(model.json())

    def _parse(self, items: list[schemas.BaseModel]) -> list[dict]:
        """
        Schema models know how to convert to json special fields.
        Convert to json and back from it so we can pass data to the client
        which is not aware of special data fields.
        """
        return [self._to_dict(i) for i in items]

    def delete_room(self, room_id: str):
        ref = self.realtime.reference(f'rooms/{room_id}')
        ref.delete()

    def set_room_attendees(self, room: schemas.Room):
        ref = self.realtime.reference(f'rooms/{room.id}/attendees')
        attendees = self._get_attendees(room.id)
        attendees = self._parse(attendees)
        if attendees:
            ref.set(attendees)

    def set_room_queue(self, room: schemas.Room):
        ref = self.realtime.reference(f'rooms/{room.id}/queue')
        attendees = self._get_in_queue(room.id)
        attendees = self._parse(attendees)
        if attendees:
            ref.set(attendees)

    def set_room(self, room: schemas.Room) -> schemas.RealtimeRoom:
        ref = self.realtime.reference('rooms')
        ref.update({
            room.id:
                {
                    'profile_id': room.profile_id,
                    'name': room.name,
                }
        })
        self.set_room_attendees(room)
        self.set_room_queue(room)

        return self.get_room(room)

    def get_room(self, room: schemas.Room) -> schemas.RealtimeRoom:
        ref = self.realtime.reference(f'rooms/{room.id}')
        return schemas.RealtimeRoom.parse_obj(ref.get())

    def set_answering(
        self,
        room: schemas.Room,
        attendee: Optional[schemas.Attendee] = None,
    ):
        ref = self.realtime.reference(f'rooms/{room.id}/answering')
        if not attendee:
            ref.delete()
        else:
            ref.update(self._to_dict(attendee))
