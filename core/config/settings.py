from pathlib import Path

from core.config.secret import Secrets
from core.config.exceptions import ConfigurationError


class Settings:
    """ Centralized configuration class that loads settings from environment variables and secrets, builds important paths, and validates critical values. """
    def __init__(self):

        self.project_root = Path(__file__).resolve().parents[2]

        self._load_environment()

        self._build_paths()

        self._validate()

    # ==================================
    # ENVIRONMENT
    # ==================================
    """ Loads configuration values from environment variables and secrets. """
    def _load_environment(self):

        self.app_env = (
            Secrets.APP_ENV or "development"
        ).lower()

        # Database

        self.database_host = Secrets.DATABASE_HOST
        self.database_port = int(
            Secrets.DATABASE_PORT or 5432
        )

        self.database_name = Secrets.DATABASE_NAME
        self.database_user = Secrets.DATABASE_USER
        self.database_password = Secrets.DATABASE_PASSWORD

        # API Keys

        self.twelvedata_api_key = (
            Secrets.TWELVEDATA_API_KEY
        )

        self.polygon_api_key = (
            Secrets.POLYGON_API_KEY
        )

        self.alphavantage_api_key = (
            Secrets.ALPHAVANTAGE_API_KEY
        )

        # Security

        self.secret_key = Secrets.SECRET_KEY

        # Logging

        self.log_level = "INFO"

        # Workers

        self.max_download_workers = 5

        self.max_retries = 3

        self.request_timeout = 30

    # ==================================
    # PATHS
    # ==================================
    """ Builds important directory paths based on the project root. """

    def _build_paths(self):

        self.data_dir = (
            self.project_root / "data"
        )

        self.raw_data_dir = (
            self.data_dir / "raw"
        )

        self.processed_data_dir = (
            self.data_dir / "processed"
        )

        self.features_dir = (
            self.data_dir / "features"
        )

        self.models_dir = (
            self.data_dir / "models"
        )

        self.checkpoints_dir = (
            self.data_dir / "checkpoints"
        )

        self.logs_dir = (
            self.project_root / "logs"
        )

        self.temp_dir = (
            self.project_root / "temp"
        )

    # ==================================
    # VALIDATION
    # ==================================
    """ Validates critical configuration values and raises errors if any are missing or invalid. """

    def _validate(self):

        required = {
            "DATABASE_HOST": self.database_host,
            "DATABASE_NAME": self.database_name,
            "DATABASE_USER": self.database_user,
            "DATABASE_PASSWORD": self.database_password,
        }

        missing = []

        for key, value in required.items():

            if value is None or value == "":
                missing.append(key)

        if missing:

            raise ConfigurationError(
                f"Missing configuration values: "
                f"{', '.join(missing)}"
            )

        if self.app_env not in (
            "development",
            "testing",
            "production",
        ):
            raise ConfigurationError(
                f"Invalid APP_ENV: {self.app_env}"
            )

    # ==================================
    # DATABASE URL
    # ==================================
    """ Constructs the database URL from individual components. """

    @property
    def database_url(self):

        return (
            f"postgresql+psycopg2://"
            f"{self.database_user}:"
            f"{self.database_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )

    # ==================================
    # DIRECTORY CREATION
    # ==================================
    """ Creates required directories if they don't exist. """

    def create_required_directories(self):

        directories = [

            self.data_dir,

            self.raw_data_dir,

            self.processed_data_dir,

            self.features_dir,

            self.models_dir,

            self.checkpoints_dir,

            self.logs_dir,

            self.temp_dir,
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True
            )


settings = Settings()

settings.create_required_directories()
