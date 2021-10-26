import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from firebase_admin import auth
from mockfirestore import MockFirestore
from unittest.mock import MagicMock

from src import factory, crud


@pytest.fixture
def firestore():
    db = MockFirestore()
    yield db
    db.reset()


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
def app(firestore):
    api_app = factory.build_app()
    api_app.db = firestore
    return api_app


@pytest.fixture
def guest(app):
    return TestClient(app)


@pytest.fixture
def student_one(app, student_one_record):
    mock_auth = MagicMock(auth)

    mock_auth.verify_id_token.return_value = {'uid': student_one_record.uid}
    mock_auth.user = MagicMock(return_value=student_one_record)

    app.auth = mock_auth
    client = TestClient(app)
    client.headers.update(
        {'Authorization': f'Bearer {student_one_record.uid}_token'}
    )
    return client


@pytest.fixture
def instructor_one(app, instructor_one_record):
    mock_auth = MagicMock(auth)

    mock_auth.verify_id_token.return_value = {'uid': instructor_one_record.uid}
    mock_auth.user = MagicMock(return_value=instructor_one_record)

    app.auth = mock_auth
    client = TestClient(app)
    client.headers.update(
        {'Authorization': f'Bearer {instructor_one_record.uid}_token'}
    )
    return client


@pytest.fixture
def instructor_two(app, instructor_two_record):
    mock_auth = MagicMock(auth)

    mock_auth.verify_id_token.return_value = {'uid': instructor_two_record.uid}
    mock_auth.user = MagicMock(return_value=instructor_two_record)

    app.auth = mock_auth
    client = TestClient(app)
    client.headers.update(
        {'Authorization': f'Bearer {instructor_two_record.uid}_token'}
    )
    return client


@pytest.fixture
def student_one_profile(firestore, student_one_record):
    return crud.get_or_create_profile(firestore, student_one_record)


@pytest.fixture
def student_two_profile(firestore, student_two_record):
    return crud.get_or_create_profile(firestore, student_two_record)


@pytest.fixture
def instructor_one_profile(firestore, instructor_one_record):
    return crud.get_or_create_profile(firestore, instructor_one_record)


@pytest.fixture
def instructor_two_profile(firestore, instructor_two_record):
    return crud.get_or_create_profile(firestore, instructor_two_record)


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
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    return test_ref, alpha_ref, bravo_ref
