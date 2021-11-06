from fastapi import Request
from firebase_admin import auth, firestore, messaging


def messaging_transport(request: Request):
    return request.app.messaging_transport


def auth_transport(request: Request):
    return request.app.auth_transport


def firestore_transport(request: Request):
    return request.app.firestore_transport


def add_dependencies(app):
    app.auth_transport = auth
    app.firestore_transport = firestore.client()
    app.messaging_transport = messaging
    return app
