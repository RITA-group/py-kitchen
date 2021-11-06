from freezegun import freeze_time
from unittest.mock import ANY


def test_list_rooms(
    student_one,
    rooms,
    instructor_one_profile,
    instructor_two_profile,
):
    response = student_one.get("/api/v1/rooms")
    assert response.status_code == 200
    assert response.json() == {
        "cursor": "not-implemented",
        'result': [
            {
                'id': ANY,
                'name': 'test room 1',
                'profile_id': instructor_one_profile.id,
                'created': '2021-01-01T00:00:00',
            },
            {
                'id': ANY,
                'name': 'test room 2',
                'profile_id': instructor_two_profile.id,
                'created': '2021-01-02T00:00:00',
            },
        ]
    }


@freeze_time('2021-01-01')
def test_create_room(instructor_one, instructor_one_profile):
    response = instructor_one.post(
        "/api/v1/rooms",
        json={'name': 'test msd room'},
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'name': 'test msd room',
        'profile_id': instructor_one_profile.id,
        'created': '2021-01-01T00:00:00',
    }


@freeze_time('2021-01-01')
def test_create_room_name_too_short(instructor_one, instructor_one_profile):
    response = instructor_one.post(
        "/api/v1/rooms",
        json={'name': 't'},
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail':
            [
                {
                    'ctx': {'limit_value': 3},
                    'loc': ['body', 'name'],
                    'msg': 'ensure this value has at least 3 characters',
                    'type': 'value_error.any_str.min_length',
                }
            ]
    }


def test_delete_room(instructor_one, rooms, firestore):
    response = instructor_one.delete(f"/api/v1/rooms/{rooms[0].id}")
    assert response.status_code == 204

    rooms_left = list(firestore.collection('rooms').stream())
    assert len(rooms_left) == 1
    assert rooms_left[0].to_dict() == rooms[1].get().to_dict()


def test_delete_other_owner_room_failure(instructor_one, rooms, firestore):
    response = instructor_one.delete(f"/api/v1/rooms/{rooms[1].id}")
    assert response.status_code == 401
    assert response.json() == {
        'detail': f"Room {rooms[1].id} doesn't belong to current user."
    }

    rooms_left = list(firestore.collection('rooms').stream())
    assert len(rooms_left) == 2

