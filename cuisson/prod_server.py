import logging
import sys

from uvicorn import Config, Server
from loguru import logger

from fastapi import FastAPI

LOG_LEVEL = logging.INFO
JSON_LOGS = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])


# TODO: move to settings
prefix = '/api/v1'
description = """
🚀 This API allows to manage rooms, profiles, and participants.

Another version of the [docs](/api/v1/redoc).

## Initial release
* **Create and delete rooms**.
* **Manage Profiles**. Profile requests must contain authentication token.
* **Add participants** (_not implemented_).
* **Raise/lower hand** (_not implemented_).

## Authentication
At this point only Google auth is enabled. Profile endpoint looks into Authorization header and validates
the token using firebase auth. Room endpoint uses test profile and doesn't check for authorization for now.
It can be enabled when we get Profile endpoint working with auth.

Checkout this [example](https://cloud.google.com/endpoints/docs/openapi/authenticating-users-firebase#making_an_authenicated_call_to_an_endpoints_api)
of how to form the auth header.
"""


if __name__ == '__main__':
    from main import app_router

    app = FastAPI(
        title='RITA API',
        description=description,
        version="0.0.1",
        openapi_url=prefix + '/openapi.json',
        docs_url=prefix + '/',
        redoc_url=prefix + '/redoc',
    )
    app.include_router(
        app_router,
        prefix=prefix,
    )
    server = Server(
        Config(
            app,
            host="0.0.0.0",
            port=8080,
            log_level=LOG_LEVEL,
        ),
    )

    setup_logging()
    server.run()
