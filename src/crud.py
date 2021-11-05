from typing import Optional
from datetime import datetime
from enum import Enum
from firebase_admin.auth import UserRecord
from google.cloud.firestore import Client as FirestoreDb
from google.cloud.firestore import DocumentSnapshot, Query, Increment

import schemas


class NotFound(Exception):
    pass


class AlreadyExists(Exception):
    pass


def data_from_snapshot(doc: DocumentSnapshot) -> dict:
    data = {'id': doc.id}
    for key, value in doc.to_dict().items():
        if hasattr(value, 'id'):
            value = value.id
        data[key] = value
    return data


def get_or_create_profile(
    db: FirestoreDb,
    user_info: UserRecord
) -> schemas.Profile:
    ref = db.collection('profiles').document(user_info.uid)
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
    return schemas.Profile(**data_from_snapshot(snapshot))


def list_rooms(db: FirestoreDb):
    query = db.collection('rooms').order_by('created').stream()
    rooms = [schemas.Room(**data_from_snapshot(doc)) for doc in query]
    return rooms


def create_room(
    db: FirestoreDb,
    new_room: schemas.RoomCreate,
    profile: schemas.Profile,
) -> schemas.Room:
    ref = db.collection('rooms').document()
    ref.set({
        'name': new_room.name,
        'profile_id': profile.id,
        'created': datetime.now()
    })
    return schemas.Room(**data_from_snapshot(ref.get()))


def get_room(
    db: FirestoreDb,
    room_id: str,
) -> schemas.Room:
    doc = db.collection('rooms').document(room_id).get()
    if not doc.exists:
        raise NotFound()
    return schemas.Room(**data_from_snapshot(doc))


def delete_room(
    db: FirestoreDb,
    room_id: str,
) -> None:
    db.collection('rooms').document(room_id).delete()


def list_attendees(
    db: FirestoreDb,
    limit: int,
    room_id: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> list[schemas.Attendee]:
    query = db.collection('attendees')
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

    return [schemas.Attendee(**data_from_snapshot(doc)) for doc in docs]


def create_attendee(
    db: FirestoreDb,
    room_id: str,
    profile: schemas.Profile,
) -> schemas.Attendee:
    attendee = db.collection('attendees').document()
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
    return schemas.Attendee(
        **data_from_snapshot(attendee.get())
    )


def delete_attendee(
    db: FirestoreDb,
    attendee_id: str,
) -> None:
    db.collection('attendees').document(attendee_id).delete()


def get_attendee(
    db: FirestoreDb,
    attendee_id: str,
) -> schemas.Attendee:
    doc = db.collection('attendees').document(attendee_id).get()
    if not doc.exists:
        raise NotFound()
    return schemas.Attendee(**data_from_snapshot(doc))


def stop_all_answers(
    db: FirestoreDb,
    room_id: str,
) -> None:
    query = db.collection('attendees').where(
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


def start_answer(
    db: FirestoreDb,
    attendee_id: str,
):
    ref = db.collection('attendees').document(attendee_id)
    ref.update(
        {
            'answering': True,
            'hand_up': False,
        }
    )


def hand_toggle(
    db: FirestoreDb,
    attendee: schemas.Attendee,
) -> schemas.Attendee:
    ref = db.collection('attendees').document(attendee.id)
    ref.update(
        {
            'hand_up': not attendee.hand_up,
            'hand_change_timestamp': datetime.now(),
        }
    )
    return schemas.Attendee(**data_from_snapshot(ref.get()))


def attendees_in_queue(
    db: FirestoreDb,
    room_id: str,
    limit: int = 100
) -> list[schemas.Attendee]:
    query = db.collection('attendees')
    query = query.where(
        'room_id', '==', room_id
    ).where(
        'hand_up', '==', True
    ).limit(limit)
    docs = list(query.stream())

    return [schemas.Attendee(**data_from_snapshot(doc)) for doc in docs]


class OrderTypes(str, Enum):
    least_answers: str = "least_answers"
    # first_arrived: str = "first_arrived"
    # random_in_queue: str = "random_in_queue"
    # random_in_room: str = "random_in_room"
    specific_attendee: str = "specific_attendee"


class NextAttendee:
    def __init__(
        self,
        db: FirestoreDb,
        room_id: str,
        attendee: Optional[schemas.Attendee] = None
    ):
        self.db = db
        self.query = db.collection('attendees').where(
            'room_id', '==', room_id
        )
        self.attendee = attendee

    def __call__(self, order: OrderTypes) -> schemas.Attendee:
        func = getattr(self, f'_{order.name}')
        doc = func()
        if not doc:
            raise NotFound
        return schemas.Attendee(**data_from_snapshot(doc))

    def _specific_attendee(self):
        # reload attendee info
        doc = self.db.collection('attendees').document(self.attendee.id).get()
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


def list_notification_tokens(
    db: FirestoreDb,
    profile_id: Optional[str] = None,
) -> list[schemas.NotificationToken]:
    query = db.collection('notification_tokens')
    query = query.where(
        'profile_id', '==', profile_id
    )
    docs = list(query.stream())

    return [schemas.NotificationToken(**data_from_snapshot(doc)) for doc in docs]


def get_notification_token(
    db: FirestoreDb,
    token: str,
) -> schemas.NotificationToken:
    ref = db.collection('notification_tokens').document(token)
    doc = ref.get()
    if not doc.exists:
        raise NotFound

    return schemas.NotificationToken(
        **data_from_snapshot(doc)
    )


def create_notification_token(
    db: FirestoreDb,
    profile: schemas.Profile,
    token: str,
) -> schemas.NotificationToken:
    ref = db.collection('notification_tokens').document(token)
    ref.set({
        'profile_id': profile.id,
        'created': datetime.now(),
        'message_count': 0,
        'last_message_timestamp': None,
    })
    doc = ref.get()
    return schemas.NotificationToken(
        **data_from_snapshot(doc)
    )


def update_token_info(
    db: FirestoreDb,
    tokens: list[schemas.NotificationToken],
):
    for token in tokens:
        ref = db.collection('notification_tokens').document(token.id)
        ref.update({
            'message_count': Increment(1),
            'last_message_timestamp': datetime.now()
        })


def delete_notification_token(
    db: FirestoreDb,
    token: str,
) -> None:
    db.collection('notification_tokens').document(token).delete()

