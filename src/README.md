🚀 This API allows managing rooms, profiles, and participants.


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
