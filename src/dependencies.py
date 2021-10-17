from fastapi import Request, HTTPException, status, Depends

import settings
import crud

from firebase_admin.auth import UserRecord, UserNotFoundError

def get_auth(request: Request):
    return request.app.auth


def get_db(request: Request):
    return request.app.db


def uid_from_authorization_token(
        request: Request,
) -> str:
    header = request.headers.get("Authorization", None)

    if not header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not provided."
        )

    token = header.split(" ")[1]
    try:
        decoded_token = request.app.auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authentication error {repr(e)}"
        )
    return decoded_token['uid']


def get_user(
        uid: str = Depends(uid_from_authorization_token),
        auth=Depends(get_auth)
) -> UserRecord:
    try:
        user_record = auth.get_user(uid)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User is not registered with the app: {repr(e)}"
        )

    return user_record


class UserProfile:
    def __init__(self, test: bool = False):
        self.test = test

    def __call__(self, request: Request):
        # TODO: remove after client auth is implemented
        if self.test:
            uid = settings.test_uid
            user_info = UserRecord({
                'localId': uid,
                'displayName': 'Test Testovich',
                'email': 'donotemailme@test.com',
                #'phoneNumber': '11111111',
            })
            return crud.get_or_create_profile(
                request.app.db,
                user_info
            )

        user_info = get_user()

        return crud.get_or_create_profile(
            request.app.db,
            user_info
        )
