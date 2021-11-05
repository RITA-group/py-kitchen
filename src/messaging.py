from fastapi import Request, Depends
from google.cloud.firestore import Client as FirestoreDb
from firebase_admin import messaging as messaging_transport

import dependencies
import crud
import schemas


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

    def send(
        self,
        tokens: list[schemas.NotificationToken],
        data: dict
    ):
        message = self.transport.MulticastMessage(
            data=data,
            tokens=[t.id for t in tokens],
        )
        response = self.transport.send_multicast(message)
        if response.success_count < len(tokens):
            # TODO: handle not delivered messages
            #raise RuntimeError
            pass

        crud.update_token_info(self.db, tokens)

    def maybe_notify_instructor(
        self,
        attendee: schemas.Attendee
    ) -> bool:
        if attendee.hand_up is False:
            # Not raising hand
            return False

        in_queue = crud.attendees_in_queue(
            self.db, attendee.room_id, limit=2
        )
        if len(in_queue) >= 2:
            # at least 2 attendees in queue
            return False

        room = crud.get_room(self.db, attendee.room_id)
        tokens = crud.list_notification_tokens(self.db, room.profile_id)
        if not tokens:
            # Profile has no associated notification tokens
            return False

        # TODO: filter out tokens that we used recently (less then 5 seconds)
        self.send(tokens, {'hand_up': attendee.name})
        return True
