import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from firebase_admin.auth import UserRecord, UserNotFoundError

import firestore
import services


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)


def uid_from_authorization_token(
    auth=Depends(services.auth_transport),
    token: str = Depends(oauth2_scheme),
) -> str:
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as e:
        # verify_id_token can raise a bunch of different errors
        # For now we just catch them all and report it in detail with 401 status.
        msg = f"Invalid authentication credentials: {repr(e)}"
        logger.warning(msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},

        )
    return decoded_token['uid']


def user_record(
    uid: str = Depends(uid_from_authorization_token),
    auth=Depends(services.auth_transport)
) -> UserRecord:
    try:
        record = auth.get_user(uid)
    except UserNotFoundError as e:
        msg = f"User is not registered with the app: {repr(e)}"
        logger.warning(f"User is not registered with the app: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
        )
    return record


class Auth:
    def __init__(
        self,
        firebase_auth=Depends(services.auth_transport),
        user: UserRecord = Depends(user_record),
        crud: firestore.Crud = Depends(),
    ):
        self.profile = crud.get_or_create_profile(user)
        self._transport = firebase_auth
