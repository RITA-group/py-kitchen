from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from dataclasses import dataclass
from google.cloud.firestore import DocumentReference
from google.cloud.firestore import DocumentSnapshot

#client = firestore.Client()

"""
firestore.DocumentSnapshot
[
'_client', 
'_data', '_exists', '_reference', '_to_protobuf', 
'create_time', 'exists', 'get', 'id', 'read_time', 'reference', 
'to_dict', 'update_time']

"""




#profiles = client.collection('profiles')
#rooms = client.collection('rooms')
#attendees = client.collection('attendees')


@dataclass
class FirebaseCollections:
    profiles: callable
    rooms: callable
    attendees: callable


#DB = FirebaseCollections(
#    profiles=client.collection('profiles'),
#    rooms=client.collection('rooms'),
#    attendees=client.collection('attendees'),
#)


class Firebase(BaseModel):
    id: str

    @classmethod
    def from_snapshot(cls, doc: DocumentSnapshot):
        data = {'id': doc.id}
        for key, value in doc.to_dict().items():
            if isinstance(value, DocumentReference):
                value = value.id
            data[key] = value
        return cls(**data)

    @classmethod
    def from_id(cls, obj_type: str, obj_id: str):
        doc = client.document(f'{obj_type}/{obj_id}').get()
        if not doc.exists:
            raise NotFound()
        return cls.from_snapshot(doc)


class Profile(Firebase):
    display_name: str
    notification_token: Optional[str]



class Room(Firebase):
    name: str
    owner_id: str
    created: datetime

    @classmethod
    def save_data(
            cls,
            ref: DocumentReference,
            name: str,
            owner_id: str
    ):
        ref.set({
            'name': name,
            #'owner_id': client.document(f'profile/{owner_id}'),
        })


class Attendee(Firebase):
    name: str
    profile_id: str
    room_id: str
    created: datetime
    # Active fields
    hand_up: bool = False
    hand_change_timestamp: Optional[datetime] = None
    answers: int = 0
    room_owner_likes: int = 0
    peer_likes: int = 0

