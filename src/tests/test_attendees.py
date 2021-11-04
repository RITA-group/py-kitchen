from freezegun import freeze_time
from datetime import datetime
from unittest.mock import ANY


def test_list_all_attendees(instructor_one, attendees):
    response = instructor_one.get("/api/v1/attendees/")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'Test Student One',
                'profile_id': ANY,
                'room_id': ANY,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answering': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
            {
                'id': ANY,
                'name': 'Test Student Two',
                'profile_id': ANY,
                'room_id': ANY,
                'created': '2021-01-02T00:00:00',
                'hand_up': False,
                'answering': False,
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
                'answering': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            }
        ],
    }


def test_list_attendees_in_room(instructor_one, rooms, attendees):
    response = instructor_one.get(f"/api/v1/attendees/?room_id={rooms[0].id}")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'Test Student One',
                'profile_id': ANY,
                'room_id': rooms[0].id,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answering': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
            {
                'id': ANY,
                'name': 'Test Student Two',
                'profile_id': ANY,
                'room_id': rooms[0].id,
                'created': '2021-01-02T00:00:00',
                'hand_up': False,
                'answering': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
        ],
    }


def test_list_attendees_with_limit(instructor_one, rooms, attendees):
    response = instructor_one.get("/api/v1/attendees/?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        'cursor': 'not-implemented',
        'result': [
            {
                'id': ANY,
                'name': 'Test Student One',
                'profile_id': ANY,
                'room_id': rooms[0].id,
                'created': '2021-01-03T00:00:00',
                'hand_up': False,
                'answering': False,
                'answers': 0,
                'room_owner_likes': 0,
                'peer_likes': 0,
                'hand_change_timestamp': None,
            },
        ],
    }


@freeze_time('2021-01-01')
def test_create_attendee(student_one, student_one_profile, rooms):
    response = student_one.post(
        "/api/v1/attendees",
        json={'room_id': rooms[1].id},
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'profile_id': student_one_profile.id,
        'room_id': rooms[1].id,
        'answers': 0,
        'created': '2021-01-01T00:00:00',
        'hand_change_timestamp': None,
        'hand_up': False,
        'answering': False,
        'name': student_one_profile.display_name,
        'peer_likes': 0,
        'room_owner_likes': 0
    }


def test_get_attendee(student_one, student_one_profile, rooms, attendees):
    response = student_one.get(f"/api/v1/attendees/{attendees[0].id}")
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'profile_id': student_one_profile.id,
        'room_id': ANY,
        'answers': 0,
        'created': '2021-01-03T00:00:00',
        'hand_change_timestamp': None,
        'hand_up': False,
        'answering': False,
        'name': student_one_profile.display_name,
        'peer_likes': 0,
        'room_owner_likes': 0,
    }


def test_delete_attendee(student_one, rooms, attendees, firestore):
    attendee_id = attendees[0].id
    response = student_one.delete(f"/api/v1/attendees/{attendee_id}")
    assert response.status_code == 204

    ref = firestore.collection('attendees').document(attendee_id)
    doc = ref.get()
    assert not doc.exists


def test_delete_other_owner_attendee_failure(student_one, rooms, attendees, firestore):
    attendee_id = attendees[1].id
    response = student_one.delete(f"/api/v1/attendees/{attendee_id}")
    assert response.status_code == 401

    ref = firestore.collection('attendees').document(attendee_id)
    doc = ref.get()
    assert doc.exists


@freeze_time('2021-01-04')
def test_attendee_hand_toggle(
        student_one,
        student_one_profile,
        attendees,
):
    response = student_one.put(
        f"/api/v1/attendees/{attendees[0].id}/hand_toggle",
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'profile_id': student_one_profile.id,
        'room_id': ANY,
        'answers': 0,
        'created': '2021-01-03T00:00:00',
        'hand_change_timestamp': '2021-01-04T00:00:00',
        'hand_up': True,
        'answering': False,
        'name': student_one_profile.display_name,
        'peer_likes': 0,
        'room_owner_likes': 0,
    }
    doc_fields = attendees[0].get().to_dict()
    assert doc_fields['hand_up'] is True
    assert doc_fields['hand_change_timestamp'] == datetime(2021, 1, 4)


@freeze_time('2021-01-04')
def test_attendee_hand_toggle_permission_error(
        student_one,
        student_one_profile,
        attendees,
):
    response = student_one.put(
        f"/api/v1/attendees/{attendees[1].id}/hand_toggle",
    )
    assert response.status_code == 401
    assert response.json() == {
        'detail': f"Attendee {attendees[1].id} doesn't belong to current user."
    }

    doc_fields = attendees[1].get().to_dict()
    assert doc_fields['hand_up'] is False
    assert doc_fields['hand_change_timestamp'] is None

