import pytest
from unittest.mock import ANY
from datetime import datetime
from firebase_admin import auth

from src import crud


@pytest.fixture
def current_answer(firestore, rooms):
    profile = crud.get_or_create_profile(
        firestore,
        auth.UserRecord({
            'localId': 'current_answer',
            'displayName': 'Current Answer',
            'email': 'donotemailme@test.com',
        })
    )
    _, ref = firestore.collection('attendees').add({
        'name': profile.display_name,
        'profile_id': profile.id,
        'room_id': rooms[0].id,
        'created': datetime(2021, 1, 4),
        'hand_up': False,
        'answering': True,
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    return ref


@pytest.fixture
def in_queue(firestore, attendees):
    attendees[0].update(
        {
            'hand_up': True,
            'answers': 1,
        }
    )
    attendees[1].update(
        {
            'hand_up': True,
        }
    )
    return attendees


def test_least_answers_first(
    instructor_one,
    in_queue,
    current_answer,
    room_one,
):
    response = instructor_one.get(
        f"/api/v1/rooms/{room_one.id}/next_attendee?order=least_answers"
    )
    assert response.status_code == 200
    assert response.json() == {
        'answering': True,
        'answers': 1,
        'created': '2021-01-03T00:00:00',
        'hand_change_timestamp': None,
        'hand_up': False,
        'id': ANY,
        'name': 'Test Student One',
        'peer_likes': 0,
        'profile_id': 'student_one',
        'room_id': room_one.id,
        'room_owner_likes': 0
    }
    previous = current_answer.get().to_dict()
    assert previous['answering'] is False
    assert previous['answers'] == 1
