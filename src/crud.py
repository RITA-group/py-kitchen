from datetime import datetime
from firebase_admin.auth import UserRecord
from google.cloud.firestore import Client as FirestoreDb
from google.cloud.firestore import DocumentSnapshot, DocumentReference

import schemas


class NotFound(Exception):
    pass


def data_from_snapshot(doc: DocumentSnapshot) -> dict:
    data = {'id': doc.id}
    for key, value in doc.to_dict().items():
        if hasattr(value, 'id'):
            value = value.id
        data[key] = value
    print(data)
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
        'owner_id': db.document(f'profiles/{profile.id}'),
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
):
    db.collection('rooms').document(room_id).delete()