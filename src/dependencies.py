from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

import controller
import schemas
import services

from firebase_admin.auth import UserRecord, UserNotFoundError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def uid_from_authorization_token(
    auth=Depends(services.auth_transport),
    token: str = Depends(oauth2_scheme),
) -> str:
    try:
        decoded_token = auth.verify_id_token(token)
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
    auth=Depends(services.auth_transport)
) -> UserRecord:
    try:
        user_record = auth.get_user(uid)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User is not registered with the app: {repr(e)}"
        )

    return user_record


def profile(
    crud: controller.Crud = Depends(),
    user_record=Depends(user),
) -> schemas.Profile:
    return crud.get_or_create_profile(user_record)
