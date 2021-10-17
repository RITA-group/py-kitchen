import pytest
from freezegun import freeze_time
from unittest.mock import ANY
from datetime import datetime


@pytest.fixture
def rooms(firestore):
    firestore.collection('rooms').add({
        'name': 'test room 1',
        'owner_id': 'some-test-id',
        'created': datetime(2021, 1, 1),
    })
    firestore.collection('rooms').add({
        'name': 'test room 2',
        'owner_id': 'some-test-id',
        'created': datetime(2021, 1, 2),
    })


def test_list_rooms(client, rooms):
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 200
    assert response.json() == {
        "cursor": "not-implemented",
        'result': [
            {
                'id': ANY,
                'name': 'test room 1',
                'owner_id': 'some-test-id',
                'created': '2021-01-01T00:00:00',
            },
            {
                'id': ANY,
                'name': 'test room 2',
                'owner_id': 'some-test-id',
                'created': '2021-01-02T00:00:00',
            },
        ]
    }


@freeze_time('2021-01-01')
def test_create_room(client):
    response = client.post(
        "/api/v1/rooms/",
        json={'name': 'test msd room'},
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': ANY,
        'name': 'test msd room',
        'owner_id': 'testtesttest',
        'created': '2021-01-01T00:00:00',
    }
