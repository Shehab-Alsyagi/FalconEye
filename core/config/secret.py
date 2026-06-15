from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

if not ENV_FILE.exists():
    raise FileNotFoundError(
        f".env file not found: {ENV_FILE}"
    )

load_dotenv(ENV_FILE)


class Secrets:

    APP_ENV = os.getenv("APP_ENV")

    POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER")
    POSTGRES_ADMIN_DB = os.getenv("POSTGRES_ADMIN_DB")
    POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD")
    AUTO_CREATE_DATABASE = os.getenv("AUTO_CREATE_DATABASE")

    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

    TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

    SECRET_KEY = os.getenv("SECRET_KEY")

    DB_POOL_SIZE = os.getenv("DB_POOL_SIZE")
    DB_MAX_OVERFLOW = os.getenv("DB_MAX_OVERFLOW")
    DB_POOL_RECYCLE = os.getenv("DB_POOL_RECYCLE")
    DB_POOL_TIMEOUT = os.getenv("DB_POOL_TIMEOUT")
    DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING")

    DB_ECHO = os.getenv("DB_ECHO")
