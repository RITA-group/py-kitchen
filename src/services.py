from fastapi import Request, FastAPI
from firebase_admin import auth, firestore, messaging, db
import config


def messaging_transport(request: Request):
    return request.app.messaging_transport


def auth_transport(request: Request):
    return request.app.auth_transport


def firestore_transport(request: Request):
    return request.app.firestore_transport


def realtime_db_transport(request: Request):
    return request.app.realtime_db_transport


def settings(request: Request):
    return request.app.settings


def connect(
    app: FastAPI,
    auth_module=auth,
    firestore_module=firestore,
    messaging_module=messaging,
    app_settings=config.get_settings(),
):
    app.auth_transport = auth_module
    app.firestore_transport = firestore_module.client()
    app.messaging_transport = messaging_module
    app.realtime_db_transport = db
    app.settings = app_settings
