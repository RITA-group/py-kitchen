import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from firebase_admin import auth
from mockfirestore import MockFirestore
from unittest.mock import MagicMock

from src import factory


@pytest.fixture
def firestore():
    db = MockFirestore()
    yield db
    db.reset()


@pytest.fixture
def auth_module():
    mock_module = MagicMock(auth)

    mock_module.verify_id_token.return_value = {
        'uid': 'base-test-token',
    }
    return mock_module


@pytest.fixture
def app(auth_module, firestore):
    api_app = factory.build_app()
    api_app.db = firestore
    api_app.auth = auth_module
    return api_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def rooms(firestore):
    _, alpha_ref = firestore.collection('rooms').add({
        'name': 'test room 1',
        'profile_id': 'testtesttest',
        'created': datetime(2021, 1, 1),
    })
    _, bravo_ref = firestore.collection('rooms').add({
        'name': 'test room 2',
        'profile_id': 'some-test-id',
        'created': datetime(2021, 1, 2),
    })

    return alpha_ref, bravo_ref


