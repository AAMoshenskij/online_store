from datetime import timedelta, datetime

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pyotp import TOTP

from apps.accounts.models import User, UserVerification
from apps.accounts.services.user import UserManager
from config.settings import AppConfig
from typing import Union


class TokenService:
    """
    Manage "jwt-token" or "otp-token" that used for authentication.
    """

    user: Union[User, None]
    user_id: int

    app_config = AppConfig.get_config()

    ALGORITHM = "HS256"
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="accounts/login")
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials.",
                                          headers={"WWW-Authenticate": "Bearer"})

    def __init__(self, user: Union[int, User, None] = None):
        if user is not None:
            if isinstance(user, User):
                self.user = user
                self.user_id = user.id
            else:
                self.user = None
                self.user_id = user

    # --------------------
    # --- Access Token ---
    # --------------------

    """
    Utility class for handling JWT authentication and access tokens.

    A user's access token will be expired due to actions such as "resetting the password," "changing the password," or
    even "logging out" (logout mechanism).

    The `access-token` stored in the database serves as a flag for the logout mechanism, ensuring that when a user
    wants to log out of the system, the current token will no longer be valid.
    """

    def create_access_token(self) -> str:
        """
        Create a new access token for the provided user.

        Returns:
            str: Access token string.
        """
        #print(f"Creating token for user {self.user_id}")  # Логируем
        # --- set data to encode ---
        to_encode = {'user_id': self.user_id}

        # --- set expire date ---
        to_encode.update({"exp": datetime.utcnow() + timedelta(self.app_config.access_token_expire_minutes)})

        # --- generate access token ---
        access_token = jwt.encode(to_encode, self.app_config.secret_key, algorithm=self.ALGORITHM)
        #print(f"Token created: {access_token}")  # Логируем
        self.update_access_token(access_token)
        return access_token

    def update_access_token(self, token: str):
        UserVerification.update(UserVerification.filter(UserVerification.user_id == self.user_id).first().id,
                                active_access_token=token)

    def reset_access_token(self):
        UserVerification.update(UserVerification.filter(UserVerification.user_id == self.user_id).first().id,
                                active_access_token=None)

    @classmethod
    async def fetch_user(cls, token: str) -> User:
        """
        Retrieve the user associated with the provided JWT token.

        Args:
            token (str): JWT token.

        Returns:
            User: User object if the token is valid, raises HTTPException if not.
        """
        print(f"Starting token verification for token: {token}")
        # --- validate token ---
        try:
            payload = jwt.decode(token, cls.app_config.secret_key, algorithms=[cls.ALGORITHM])
            print(f"Token payload: {payload}")
        except JWTError as e:
            raise cls.credentials_exception

        # --- validate payloads in token ---
        user_id = payload.get("user_id")
        if user_id is None:
            print("No user_id in token")
            raise cls.credentials_exception

        # --- get user ---
        # TODO move user data to token and dont fetch them from database
        user = UserManager.get_user(user_id)
        if user is None:
            print(f"User {user_id} not found")
            raise cls.credentials_exception
        
        print(f"User found: {user.email}")

        UserManager.is_active(user)

        # --- validate access token ---
        #active_access_token = UserVerification.filter(UserVerification.user_id == user_id).first().active_access_token
        #if token != active_access_token:
        #    raise cls.credentials_exception

        UserManager.is_active(user)
        return user

    # -----------------
    # --- OTP Token ---
    # -----------------

    @classmethod
    def create_otp_token(cls):
        totp = TOTP(cls.app_config.otp_secret_key, interval=cls.app_config.otp_expire_seconds)
        return totp.now()

    def request_is_register(self):
        """
        Will be used just when a new user is registered.
        """

        UserVerification.create(user_id=self.user_id, request_type='register')

    def get_new_email(self):
        _change: UserVerification = UserVerification.filter(UserVerification.user_id == self.user_id).first()
        if _change.request_type == 'change-email':
            return _change.new_email
        return False

    def request_is_change_email(self, new_email: str):
        _change = UserVerification.filter(UserVerification.user_id == self.user_id).first().id
        UserVerification.update(_change, new_email=new_email, request_type='change-email')

    def reset_is_change_email(self):
        _change = UserVerification.filter(UserVerification.user_id == self.user_id).first().id
        UserVerification.update(_change, new_email=None, request_type=None)

    def reset_is_reset_password(self):
        _change = UserVerification.filter(UserVerification.user_id == self.user_id).first().id
        UserVerification.update(_change, request_type='reset-password')

    def reset_otp_token_type(self):
        """
        Remove the request_type for otp token by set it to None.
        """

        _change = UserVerification.filter(UserVerification.user_id == self.user_id).first().id
        UserVerification.update(_change, request_type=None)

    def get_otp_request_type(self):
        return UserVerification.filter(UserVerification.user_id == self.user_id).first().request_type

    @classmethod
    def validate_otp_token(cls, token: str):
        totp = TOTP(cls.app_config.otp_secret_key, interval=cls.app_config.otp_expire_seconds)
        return totp.verify(token)

    @classmethod
    def check_time_remaining(cls):
        totp = TOTP(cls.app_config.otp_secret_key, interval=cls.app_config.otp_expire_seconds)
        time_remaining = int(totp.interval - datetime.now().timestamp() % totp.interval)
        if time_remaining != 0:
            # OTP has not expired, do not resend
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OTP not expired. Resend available in {time_remaining} seconds.")
