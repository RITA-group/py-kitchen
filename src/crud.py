from typing import Optional
from datetime import datetime
from firebase_admin.auth import UserRecord
from google.cloud.firestore import Client as FirestoreDb
from google.cloud.firestore import DocumentSnapshot, Query

import schemas


class NotFound(Exception):
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
    snapshot = ref.get()
    if not snapshot.exists:
        ref.set({
            'display_name': user_info.display_name,
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
