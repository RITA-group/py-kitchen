from firebase_admin import initialize_app as init_firebase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json_logging

import services
import config
from middleware import CacheControlHeader
from api import router


def build_app(settings: config.Settings):
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
    settings = config.get_settings()
    app = build_app(settings)
    json_logging.init_fastapi(enable_json=settings.json_logging)
    json_logging.init_request_instrument(
        app, exclude_url_patterns=[r'^/exclude_from_request_instrumentation']
    )
    init_firebase()
    services.connect(app)
    return app
