from fastapi import Depends
from firebase_admin import messaging as messaging_transport

import firestore
import services
import schemas


class Message:
    def __init__(
        self,
        crud: firestore.Crud = Depends(),
        transport: messaging_transport = Depends(services.messaging_transport)
    ):
        self.crud = crud
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

        self.crud.update_token_info(tokens)

    def maybe_notify_instructor(
        self,
        attendee: schemas.Attendee
    ) -> bool:
        if attendee.hand_up is False:
            # Not raising hand
            return False

        in_queue = self.crud.attendees_in_queue(attendee.room_id, limit=2)
        if len(in_queue) >= 2:
            # at least 2 attendees in queue
            return False

        room = self.crud.get_room(attendee.room_id)
        tokens = self.crud.list_notification_tokens(room.profile_id)
        if not tokens:
            # Profile has no associated notification tokens
            return False

        # TODO: filter out tokens that we used recently (less then 5 seconds)
        self.send(tokens, {'hand_up': attendee.name})
        return True
