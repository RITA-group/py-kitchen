from google.cloud import firestore
from pydantic import BaseModel
from pprint import pprint

db = firestore.Client()

"""
firestore.DocumentSnapshot
[
'_client', 
'_data', '_exists', '_reference', '_to_protobuf', 
'create_time', 'exists', 'get', 'id', 'read_time', 'reference', 
'to_dict', 'update_time']

"""


class NotFound(Exception):
    pass


class FirebaseMixin:
    id: str

    @staticmethod
    def collection():
        """
        Specific Firestore root collection
        """
        raise NotImplemented

    @staticmethod
    def convert_fields(data: dict) -> dict:
        """
        Convert Firestore formats to python
        """
        return {}

    @classmethod
    def from_snapshot(cls, doc: firestore.DocumentSnapshot):
        data = doc.to_dict()
        data['id'] = str(doc.id)
        data.update(cls.convert_fields(data))
        return cls(**data)

    def delete(self):
        self.collection().document(self.id).delete()

    @classmethod
    def from_id(cls, obj_id: str):
        doc = cls.collection().document(obj_id).get()
        if not doc.exists:
            raise NotFound()
        return cls.from_snapshot(doc)


class Room(FirebaseMixin, BaseModel):
    name: str
    owner: str
    token: str

    @staticmethod
    def collection():
        return db.collection(u'room')

    @staticmethod
    def convert_fields(data: dict) -> dict:
        return {
            'owner': data['owner'].path,
        }


class User(FirebaseMixin, BaseModel):
    name: str
    answer_count: int
    hand_up: bool
    is_answering: bool
    room: str

    @staticmethod
    def collection():
        return db.collection(u'user')

    @staticmethod
    def convert_fields(data: dict) -> dict:
        return {
            'room': data['room'].path,
        }
