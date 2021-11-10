import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from firebase_admin import auth, messaging
from mockfirestore import MockFirestore
from unittest.mock import MagicMock

from src import factory, schemas, services


@pytest.fixture
def firestore():
    db = MockFirestore()
    yield db
    db.reset()


@pytest.fixture
def send_multicast_success_count():
    return 0


@pytest.fixture
def messaging_transport(send_multicast_success_count):
    transport = MagicMock(messaging)
    response = MagicMock()
    response.success_count = send_multicast_success_count
    send_multicast = MagicMock(return_value=response)
    transport.send_multicast = send_multicast
    return transport


@pytest.fixture
def auth_transport():
    return MagicMock(auth)


@pytest.fixture
def student_one_record() -> auth.UserRecord:
    return auth.UserRecord({
        'localId': 'student_one',
        'displayName': 'Test Student One',
        'email': 'donotemailme@test.com',
        # 'phoneNumber': '11111111',
    })


@pytest.fixture
def student_two_record() -> auth.UserRecord:
    return auth.UserRecord({
        'localId': 'student_two',
        'displayName': 'Test Student Two',
        'email': 'donotemailme@test.com',
        # 'phoneNumber': '11111111',
    })


@pytest.fixture
def instructor_one_record() -> auth.UserRecord:
    return auth.UserRecord({
        'localId': 'instructor_one',
        'displayName': 'Test Instructor One',
        'email': 'instructorone@test.com',
        # 'phoneNumber': '11111111',
    })


@pytest.fixture
def instructor_two_record() -> auth.UserRecord:
    return auth.UserRecord({
        'localId': 'instructor_two',
        'displayName': 'Test Instructor Two',
        'email': 'instructortwo@test.com',
        # 'phoneNumber': '11111111',
    })


@pytest.fixture
def app(firestore, messaging_transport, auth_transport):
    firestore_module = MagicMock()
    firestore_module.client.return_value = firestore

    api_app = factory.build_app()
    services.connect(
        api_app,
        firestore_module=firestore_module,
        auth_module=auth_transport,
        messaging_module=messaging_transport,
    )
    return api_app


@pytest.fixture
def guest(app):
    return TestClient(app)


@pytest.fixture
def login(app, firestore, auth_transport):
    def set_transport_calls(record: auth.UserRecord):
        auth_transport.verify_id_token.return_value = {'uid': record.uid}
        auth_transport.get_user.return_value = record

        client = TestClient(app)
        client.headers.update(
            # Value for Bearer token doesn't matter because overwrite verify_id_token for testing.
            # uid here is used only for testing
            {'Authorization': f'Bearer {record.uid}_token'}
        )
        return client
    return set_transport_calls


@pytest.fixture
def student_one(student_one_record, login):
    return login(student_one_record)


@pytest.fixture
def instructor_one(instructor_one_record, login):
    return login(instructor_one_record)


@pytest.fixture
def instructor_two(instructor_two_record, login):
    return login(instructor_two_record)


@pytest.fixture
def create_profile(firestore):
    def add_profile(user_record):
        ref = firestore.collection('profiles').document(user_record.uid)
        ref.set({
            'display_name': user_record.display_name,
            'notification_token': None,
        })
        return schemas.Profile.from_snapshot(ref.get())
    return add_profile


@pytest.fixture
def student_one_profile(student_one_record, create_profile):
    return create_profile(student_one_record)


@pytest.fixture
def student_two_profile(student_two_record, create_profile):
    return create_profile(student_two_record)


@pytest.fixture
def instructor_one_profile(instructor_one_record, create_profile):
    return create_profile(instructor_one_record)


@pytest.fixture
def instructor_two_profile(instructor_two_record, create_profile):
    return create_profile(instructor_two_record)


@pytest.fixture
def rooms(firestore, instructor_one_profile, instructor_two_profile):
    _, alpha_ref = firestore.collection('rooms').add({
        'name': 'test room 1',
        'profile_id': instructor_one_profile.id,
        'created': datetime(2021, 1, 1),
    })
    _, bravo_ref = firestore.collection('rooms').add({
        'name': 'test room 2',
        'profile_id': instructor_two_profile.id,
        'created': datetime(2021, 1, 2),
    })

    return alpha_ref, bravo_ref


@pytest.fixture
def room_one(rooms):
    return rooms[0].get()


@pytest.fixture
def room_two(rooms):
    return rooms[1].get()


@pytest.fixture
def attendees(
    firestore,
    rooms,
    student_one_profile,
    student_two_profile,
):
    _, test_ref = firestore.collection('attendees').add({
        'name': student_one_profile.display_name,
        'profile_id': student_one_profile.id,
        'room_id': rooms[0].id,
        'created': datetime(2021, 1, 3),
        'hand_up': False,
        'hand_change_timestamp': None,
        'answering': False,
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    _, alpha_ref = firestore.collection('attendees').add({
        'name': student_two_profile.display_name,
        'profile_id': student_two_profile.id,
        'room_id': rooms[0].id,
        'created': datetime(2021, 1, 2),
        'hand_up': False,
        'hand_change_timestamp': None,
        'answering': False,
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    _, bravo_ref = firestore.collection('attendees').add({
        'name': 'bravo',
        'profile_id': 'bravo',
        'room_id': rooms[1].id,
        'created': datetime(2021, 1, 1),
        'hand_up': False,
        'hand_change_timestamp': None,
        'answering': False,
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    return test_ref, alpha_ref, bravo_ref
