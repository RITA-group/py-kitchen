import os

version = '0.2.1'
prefix = '/api/v1'
description = f"""
🚀 This API allows to manage rooms, profiles, and participants.

Another version of the [docs]({prefix}/redoc).

## Initial release
* **Create and delete rooms**.
* **Manage Profiles**. Profile requests must contain authentication token.
* **Add participants**.
* **Raise/lower hand**.

## Authentication
At this point only Google auth is enabled. Profile endpoint looks into Authorization header and validates
the token using firebase auth. Room endpoint uses test profile and doesn't check for authorization for now.
It can be enabled when we get Profile endpoint working with auth.

Checkout this [example](https://cloud.google.com/endpoints/docs/openapi/authenticating-users-firebase#making_an_authenicated_call_to_an_endpoints_api)
of how to form the auth header.
"""

test_uid = 'testtesttest'

origins = [
    "https://rita-iu.web.app/",
    "http://localhost",
    "http://localhost:8100",
]

api_key = os.environ.get('API_KEY', 'test_api_key')
