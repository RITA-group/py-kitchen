from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

import settings
import crud
import schemas

from firebase_admin.auth import UserRecord, UserNotFoundError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_auth(request: Request):
    return request.app.auth


def get_db(request: Request):
    return request.app.db


def uid_from_authorization_token(
        request: Request,
        token: str = Depends(oauth2_scheme),
) -> str:
    try:
        decoded_token = request.app.auth.verify_id_token(token)
    except Exception as e:
        # verify_id_token can raise a bunch of different errors
        # For now we just catch them all and report it in detail with 401 status.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {repr(e)}",
            headers={"WWW-Authenticate": "Bearer"},

        )
    return decoded_token['uid']


def user(
        uid: str = Depends(uid_from_authorization_token),
        auth=Depends(get_auth)
) -> UserRecord:
    try:
        user_record = auth.user(uid)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User is not registered with the app: {repr(e)}"
        )

    return user_record


def profile(
    db=Depends(get_db),
    user_record=Depends(user),
) -> schemas.Profile:
    return crud.get_or_create_profile(
        db,
        user_record,
    )


def test_profile(
    db=Depends(get_db),
):
    user_info = UserRecord({
        'localId': settings.test_uid,
        'displayName': 'Test Testovich',
        'email': 'donotemailme@test.com',
        # 'phoneNumber': '11111111',
    })

    return crud.get_or_create_profile(
        db,
        user_info
    )
