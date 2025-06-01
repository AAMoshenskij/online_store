import os
from pathlib import Path

# from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr



class AppConfig:
    """
    App Configuration.
    """

    class _AppConfig(BaseModel):
        app_name: str
        secret_key: str
        access_token_expire_minutes: int
        otp_secret_key: str
        otp_expire_seconds: int

    config = _AppConfig(
        app_name=os.getenv("APP_NAME", "Online Store"),
        secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        otp_secret_key=os.getenv("OTP_SECRET_KEY", "JBSWY3DPEHPK3PXP"),
        otp_expire_seconds=int(os.getenv("OTP_EXPIRE_SECONDS", "300")), )

    @classmethod
    def get_config(cls) -> _AppConfig:
        """
        Get the App configuration.
        """

        return cls.config


class EmailServiceConfig:
    """
    SMTP Configuration.
    """

    class _SMTPConfig(BaseModel):
        smtp_server: str
        smtp_port: int
        smtp_username: EmailStr
        smtp_password: str
        use_local_fallback: bool

    config = _SMTPConfig(
        smtp_server=os.getenv("SMTP_SERVER"),
        smtp_port=int(os.getenv("SMTP_PORT")),
        smtp_username=os.getenv("SMTP_USERNAME"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        use_local_fallback=os.getenv("USE_LOCAL_FALLBACK", "False").lower() == "true"
    )

    @classmethod
    def get_config(cls) -> _SMTPConfig:
        """
        Get the SMTP configuration
        """

        return cls.config


# -------------------------
# --- Database Settings ---
# -------------------------

DATABASES = {
    "drivername": os.getenv("DB_DRIVER", "postgresql"),
    "username": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME", "online_store"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

# ----------------------
# --- Media Settings ---
# ----------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"

# Ensure the "media" directory exists
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# int number as MB
MAX_FILE_SIZE = 5
products_list_limit = 12

# TODO add settings to limit register new user or close register

# Elasticsearch settings
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
