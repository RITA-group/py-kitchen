from fastapi import Request, Depends
from google.cloud.firestore import Client as FirestoreDb
from firebase_admin import messaging as messaging_transport

import dependencies
import crud


def get_transport(request: Request) -> messaging_transport:
    return request.app.messaging_transport


class Message:
    def __init__(
            self,
            db: FirestoreDb = Depends(dependencies.get_db),
            transport: messaging_transport = Depends(get_transport)
    ):
        self.db = db
        self.transport = transport

    def instructor(self, room_id: str, data: dict):
        room = crud.get_room(self.db, room_id)
        tokens = crud.list_notification_tokens(self.db, room.profile_id)
        if not tokens:
            return

        # TODO: add to conftest
        message = self.transport.MulticastMessage(
            data=data,
            tokens=[t.id for t in tokens],
        )
        # TODO: add to conftest
        response = self.transport.send_multicast(message)
        if response.success_count != len(tokens):
            # TODO: handle not delivered messages
            pass

        crud.update_token_info(self.db, tokens)

    def attendee(self, profile_id: str, data: dict):
        raise NotImplemented
