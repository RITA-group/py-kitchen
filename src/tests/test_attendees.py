from freezegun import freeze_time
from unittest.mock import ANY
from datetime import datetime
import pytest


@pytest.fixture
def attendees(rooms, firestore):
    _, test_ref = firestore.collection('attendees').add({
        'name': 'testtesttest',
        'profile_id': 'testtesttest',
        'room_id': rooms[0].id,
        'created': datetime(2021, 1, 3),
        'hand_up': False,
        'answers': 0,
        'room_owner_likes': 0,
        'peer_likes': 0
    })
    _, alpha_ref = firestore.collection('attendees').add({
        'name': 'alpha',
        'profile_id': 'alpha',
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


def test_list_all_attendees(client, attendees):
    response = client.get("/api/v1/attendees/")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'testtesttest',
                'profile_id': 'testtesttest',
                'room_id': ANY,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
            {
                'id': ANY,
                'name': 'alpha',
                'profile_id': 'alpha',
                'room_id': ANY,
                'created': '2021-01-02T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
            {
                'id': ANY,
                'name': 'bravo',
                'profile_id': 'bravo',
                'room_id': ANY,
                'created': '2021-01-01T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            }
        ],
    }


def test_list_attendees_in_room(client, rooms, attendees):
    response = client.get(f"/api/v1/attendees/?room_id={rooms[0].id}")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'testtesttest',
                'profile_id': 'testtesttest',
                'room_id': rooms[0].id,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
            {
                'id': ANY,
                'name': 'alpha',
                'profile_id': 'alpha',
                'room_id': rooms[0].id,
                'created': '2021-01-02T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
        ],
    }


def test_list_attendees_with_limit(client, rooms, attendees):
    response = client.get("/api/v1/attendees/?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'testtesttest',
                'profile_id': 'testtesttest',
                'room_id': rooms[0].id,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
        ],
    }


@freeze_time('2021-01-01')
def test_create_attendee(client, rooms):
    response = client.post(
        "/api/v1/attendees/",
        json={'room_id': rooms[1].id},
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'profile_id': 'testtesttest',
        'room_id': rooms[1].id,
        'answers': 0,
        'created': '2021-01-01T00:00:00',
        'hand_change_timestamp': None,
        'hand_up': False,
        'name': 'Test Testovich',
        'peer_likes': 0,
        'room_owner_likes': 0
    }


def test_get_attendee(client, rooms, attendees):
    response = client.get(f"/api/v1/attendees/{attendees[0].id}")
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'profile_id': 'testtesttest',
        'room_id': ANY,
        'answers': 0,
        'created': '2021-01-03T00:00:00',
        'hand_change_timestamp': None,
        'hand_up': False,
        'name': 'testtesttest',
        'peer_likes': 0,
        'room_owner_likes': 0,
    }


def test_delete_attendee(client, rooms, attendees, firestore):
    attendee_id = attendees[0].id
    response = client.delete(f"/api/v1/attendees/{attendee_id}")
    assert response.status_code == 204

    ref = firestore.collection('attendees').document(attendee_id)
    doc = ref.get()
    assert not doc.exists


def test_delete_other_owner_attendee_failure(client, rooms, attendees, firestore):
    attendee_id = attendees[1].id
    response = client.delete(f"/api/v1/attendees/{attendee_id}")
    assert response.status_code == 401

    ref = firestore.collection('attendees').document(attendee_id)
    doc = ref.get()
    assert doc.exists
