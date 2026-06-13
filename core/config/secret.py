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

    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

    TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

    SECRET_KEY = os.getenv("SECRET_KEY")
