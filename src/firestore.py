import fastapi
from enum import Enum
from fastapi import Depends
from typing import Optional, List
from datetime import datetime
from firebase_admin.auth import UserRecord
from google.cloud.firestore import Client as FirestoreDb
from google.cloud.firestore import Query, Increment

import schemas
import services


class NotFound(Exception):
    pass


class AlreadyExists(Exception):
    pass


class NoNextAttendee(Exception):
    pass


class RoomRelationTypes(str, Enum):
    joined: str = "joined"
    created: str = "created"


class Crud:
    def __init__(
        self,
        db: FirestoreDb = Depends(services.firestore_transport),
    ):
        self.db = db

    def get_or_create_profile(
        self,
        user_info: UserRecord
    ) -> schemas.Profile:
        ref = self.db.collection('profiles').document(user_info.uid)
        email = user_info.email or ''
        name_from_email, _ = email.split('@')
        name_from_email = name_from_email.replace('_', ' ')

        snapshot = ref.get()
        if not snapshot.exists:
            ref.set({
                'display_name': user_info.display_name or name_from_email,
                'notification_token': None,
            })
            snapshot = ref.get()
        return schemas.Profile.from_snapshot(snapshot)

    def list_rooms(
        self,
        profile: Optional[schemas.Profile] = None,
    ) -> List[schemas.Room]:
        query = self.db.collection('rooms').order_by('created')
        if profile:
            query = query.where('profile_id', '==', profile.id)

        rooms = [schemas.Room.from_snapshot(doc) for doc in query.stream()]
        return rooms

    def fetch_rooms(
        self,
        ids: List[str],
    ) -> List[schemas.Room]:
        query = self.db.collection('rooms')
        docs = [query.document(i).get() for i in ids]
        rooms = [schemas.Room.from_snapshot(doc) for doc in docs if doc.exists]
        return rooms

    def create_room(
        self,
        new_room: schemas.RoomCreate,
        profile: schemas.Profile,
    ) -> schemas.Room:
        ref = self.db.collection('rooms').document()
        ref.set({
            'name': new_room.name,
            'profile_id': profile.id,
            'created': datetime.now()
        })
        return schemas.Room.from_snapshot(ref.get())

    def get_room(self, room_id: str) -> schemas.Room:
        doc = self.db.collection('rooms').document(room_id).get()
        if not doc.exists:
            raise NotFound()
        return schemas.Room.from_snapshot(doc)

    def delete_room(self, room_id: str) -> None:
        self.db.collection('rooms').document(room_id).delete()

    def list_attendees(
        self,
        limit: int,
        room_id: Optional[str] = None,
        profile_id: Optional[str] = None,
    ) -> list[schemas.Attendee]:
        query = self.db.collection('attendees')
        if room_id:
            query = query.where(
                'room_id', '==', room_id
            )
        if profile_id:
            query = query.where(
                'profile_id', '==', profile_id
            )
        query = query.order_by(
            'created',
            direction=Query.DESCENDING,
        ).limit(limit)
        docs = list(query.stream())

        return [schemas.Attendee.from_snapshot(doc) for doc in docs]

    def create_attendee(
        self,
        room_id: str,
        profile: schemas.Profile,
    ) -> schemas.Attendee:
        attendee = self.db.collection('attendees').document()
        attendee.set({
            'name': profile.display_name,
            'profile_id': profile.id,
            'room_id': room_id,
            'created': datetime.now(),
            'hand_up': False,
            'answering': False,
            'answers': 0,
            'room_owner_likes': 0,
            'peer_likes': 0
        })
        return schemas.Attendee.from_snapshot(attendee.get())

    def delete_attendee(self, attendee_id: str) -> None:
        self.db.collection('attendees').document(attendee_id).delete()

    def get_attendee(self, attendee_id: str) -> schemas.Attendee:
        doc = self.db.collection('attendees').document(attendee_id).get()
        if not doc.exists:
            raise NotFound()
        return schemas.Attendee.from_snapshot(doc)

    def stop_all_answers(self, room_id: str) -> None:
        query = self.db.collection('attendees').where(
            'room_id', '==', room_id
        ).where(
            'answering', '==', True
        )
        for doc in query.stream():
            doc.reference.update(
                {
                    'answering': False,
                    'answers': Increment(1),
                }
            )

    def start_answer(self, attendee_id: str):
        ref = self.db.collection('attendees').document(attendee_id)
        ref.update(
            {
                'answering': True,
                'hand_up': False,
            }
        )

    def hand_toggle(self, attendee: schemas.Attendee) -> schemas.Attendee:
        ref = self.db.collection('attendees').document(attendee.id)
        ref.update(
            {
                'hand_up': not attendee.hand_up,
                'hand_change_timestamp': datetime.now(),
            }
        )
        return schemas.Attendee.from_snapshot(ref.get())

    def attendees_in_queue(
        self,
        room_id: str,
        limit: int = 100
    ) -> list[schemas.Attendee]:
        query = self.db.collection('attendees')
        query = query.where(
            'room_id', '==', room_id
        ).where(
            'hand_up', '==', True
        ).limit(limit)
        docs = list(query.stream())

        return [schemas.Attendee.from_snapshot(doc) for doc in docs]

    def list_notification_tokens(
        self,
        profile_id: Optional[str] = None,
    ) -> list[schemas.NotificationToken]:
        query = self.db.collection('notification_tokens')
        query = query.where(
            'profile_id', '==', profile_id
        )
        docs = list(query.stream())

        return [schemas.NotificationToken.from_snapshot(doc) for doc in docs]

    def get_notification_token(self, token: str) -> schemas.NotificationToken:
        ref = self.db.collection('notification_tokens').document(token)
        doc = ref.get()
        if not doc.exists:
            raise NotFound

        return schemas.NotificationToken.from_snapshot(doc)

    def create_notification_token(
        self,
        profile: schemas.Profile,
        token: str,
    ) -> schemas.NotificationToken:
        ref = self.db.collection('notification_tokens').document(token)
        ref.set({
            'profile_id': profile.id,
            'created': datetime.now(),
            'message_count': 0,
            'last_message_timestamp': None,
        })
        doc = ref.get()
        return schemas.NotificationToken.from_snapshot(doc)

    def update_token_info(self, tokens: list[schemas.NotificationToken]):
        for token in tokens:
            ref = self.db.collection('notification_tokens').document(token.id)
            ref.update({
                'message_count': Increment(1),
                'last_message_timestamp': datetime.now()
            })

    def delete_notification_token(self, token: str) -> None:
        self.db.collection('notification_tokens').document(token).delete()


class OrderTypes(str, Enum):
    least_answers: str = "least_answers"
    # first_arrived: str = "first_arrived"
    # random_in_queue: str = "random_in_queue"
    # random_in_room: str = "random_in_room"
    specific_attendee: str = "specific_attendee"


class NextAttendee:
    def __init__(
        self,
        room_id: str = fastapi.Path(..., title="Room id"),
        attendee_id: Optional[str] = fastapi.Query(
            None,
            title='Force a specific attendee.'
        ),
        order: OrderTypes = fastapi.Query(
            OrderTypes.least_answers,
            title='Algorithm used to pick the next attendee.'
        ),
        db: FirestoreDb = Depends(services.firestore_transport),
    ):
        self.db = db
        self.attendee_id = attendee_id
        self.order = order
        self.query = db.collection('attendees').where(
            'room_id', '==', room_id
        )

    def next_attendee(self):
        func = getattr(self, f'_{self.order.name}')
        doc = func()
        if not doc:
            raise NotFound
        return schemas.Attendee.from_snapshot(doc)

    def _specific_attendee(self):
        # reload attendee info
        ref = self.db.collection('attendees').document(self.attendee_id)
        doc = ref.get()
        if not doc.exists:
            raise NotFound
        return doc

    def _least_answers(self):
        query = self.query.where(
            'hand_up', '==', True
        ).order_by(
            'answers',
            direction=Query.DESCENDING,
        ).limit(1)
        return next(query.stream(), None)

    def _first_arrived(self):
        return None

    def _random_in_queue(self):
        return None

    def _random_in_room(self):
        return None
