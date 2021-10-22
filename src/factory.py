from firebase_admin import auth, initialize_app, firestore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware import CacheControlHeader
from api import router
import settings


def build_app():
    app = FastAPI(
        title='RITA API',
        description=settings.description,
        version=settings.version,
        openapi_url=settings.prefix + '/openapi.json',
        docs_url=settings.prefix + '/',
        redoc_url=settings.prefix + '/redoc',
    )
    app.add_middleware(CacheControlHeader, header_value='no-store')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        router,
        prefix=settings.prefix,
    )
    return app


def prod_app():
    app = build_app()
    initialize_app()
    app.auth = auth
    app.db = firestore.client()
    return app
