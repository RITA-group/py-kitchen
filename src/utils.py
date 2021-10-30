import json
import requests
import settings


def get_user_token_from(custom_token) -> dict:
    """Return a Firebase user ID token from custom token.
    This is based on:
    https://github.com/jewang/firebase-id-token-generator-python/blob/master/firebase_token_generator.py
    Returns:
      dict: Keys are
        "kind", "idToken", "refreshToken", and "expiresIn".
      "expiresIn" is in seconds.
      The return dict matches the response payload described in
      https://firebase.google.com/docs/reference/rest/auth/#section-verify-custom-token
      The actual token is at get_token(uid)["idToken"].
    """
    data = {
        'token': custom_token.decode('utf-8'),
        'returnSecureToken': True
    }

    url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty" \
          "/verifyCustomToken?key={}".format(settings.api_key)

    resp = requests.post(
        url,
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'},
    )

    return resp.json()
