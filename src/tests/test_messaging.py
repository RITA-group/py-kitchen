import pytest
from freezegun import freeze_time
from datetime import datetime


@pytest.fixture
def send_multicast_success_count():
    return 1


@pytest.fixture
def message_tokens(
        instructor_one_profile,
        instructor_two_profile,
        firestore
):
    ref_one = firestore.collection('notification_tokens').document('abc')
    ref_one.set({
        'profile_id': instructor_one_profile.id,
        'created': datetime(2021, 1, 1),
        'message_count': 0,
        'last_message_timestamp': None,
    })
    ref_two = firestore.collection('notification_tokens').document('xyz')
    ref_two.set({
        'profile_id': instructor_two_profile.id,
        'created': datetime(2021, 1, 1),
        'message_count': 0,
        'last_message_timestamp': None,
    })
    return ref_one, ref_two


@freeze_time('2021-01-04')
def test_send_message_on_hand_up(
    student_one,
    student_one_profile,
    attendees,
    message_tokens,
    messaging_transport,
):
    response = student_one.put(
        f"/api/v1/attendees/{attendees[0].id}/hand_toggle",
    )
    assert response.status_code == 200
    doc_fields = attendees[0].get().to_dict()
    assert doc_fields['hand_up'] is True
    assert doc_fields['hand_change_timestamp'] == datetime(2021, 1, 4)

    # lib call to:
    # message = messaging.MulticastMessage(
    #     data=data,
    #     tokens=tokens_list,
    # )
    assert messaging_transport.MulticastMessage.call_count == 1

    _, kwargs = messaging_transport.MulticastMessage.call_args
    assert kwargs == {
        'data': {'hand_up': 'Test Student One'},
        'tokens': ['abc']
    }
    # lib call `messaging.send_multicast(message)`
    assert messaging_transport.send_multicast.call_count == 1
    args, _ = messaging_transport.send_multicast.call_args
    assert len(args)

    token = message_tokens[0].get().to_dict()
    assert token['message_count'] == 1
    assert token['last_message_timestamp'] == datetime(2021, 1, 4)

    token = message_tokens[1].get().to_dict()
    assert token['message_count'] == 0
    assert token['last_message_timestamp'] is None


def test_list_notification_tokens(
    instructor_one,
    instructor_one_profile,
    message_tokens,
):
    response = instructor_one.get("/api/v1/profile/notification_tokens")
    assert response.status_code == 200
    assert response.json() == {
        "cursor": "not-implemented",
        'result': [
            {
                'id': 'abc',
                'profile_id': instructor_one_profile.id,
                'created': '2021-01-01T00:00:00',
                'last_message_timestamp': None,
                'message_count': 0,
            },
        ]
    }


@freeze_time('2021-01-01')
def test_create_notification_token(
    instructor_one,
    instructor_one_profile,
    firestore,
):
    response = instructor_one.post(
        "/api/v1/profile/notification_tokens",
        json={'token': 'abc'},
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': 'abc',
        'profile_id': instructor_one_profile.id,
        'created': '2021-01-01T00:00:00',
        'last_message_timestamp': None,
        'message_count': 0,
    }

    doc = firestore.collection('notification_tokens').document('abc').get()
    assert doc.to_dict() == {
        'profile_id': instructor_one_profile.id,
        'created': datetime(2021, 1, 1),
        'last_message_timestamp': None,
        'message_count': 0,
    }


def test_delete_notification_token(
    instructor_one,
    message_tokens,
    firestore,
):
    response = instructor_one.delete(
        f"/api/v1/profile/notification_tokens/abc"
    )
    assert response.status_code == 204

    doc = firestore.collection('notification_tokens').document('abc').get()
    assert not doc.exists
    doc = firestore.collection('notification_tokens').document('xyz').get()
    assert doc.exists


def test_delete_other_owner_token_failure(
    instructor_one,
    message_tokens,
    firestore,
):
    response = instructor_one.delete(
        f"/api/v1/profile/notification_tokens/xyz"
    )
    assert response.status_code == 403
    assert response.json() == {
        'detail': "Token doesn't belong to current user.",
    }

    doc = firestore.collection('notification_tokens').document('abc').get()
    assert doc.exists
    doc = firestore.collection('notification_tokens').document('xyz').get()
    assert doc.exists
