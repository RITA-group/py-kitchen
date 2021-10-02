from google.cloud import firestore


def get_users() -> dict:
    db = firestore.Client()
    users_ref = db.collection(u'user')
    docs = users_ref.stream()
    users = {doc.id: doc.to_dict() for doc in docs}
    return users
