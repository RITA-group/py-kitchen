from fastapi import Request, FastAPI
from firebase_admin import auth, firestore, messaging


def messaging_transport(request: Request):
    return request.app.messaging_transport


def auth_transport(request: Request):
    return request.app.auth_transport


def firestore_transport(request: Request):
    return request.app.firestore_transport


def connect(
    app: FastAPI,
    auth_module=auth,
    firestore_module=firestore,
    messaging_module=messaging,
):
    app.auth_transport = auth_module
    app.firestore_transport = firestore_module.client()
    app.messaging_transport = messaging_module
