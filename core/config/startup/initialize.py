"""
System initialization module for FalconEye.

Coordinates the startup process including:
- Configuration validation
- Database bootstrap (if needed)
- Table creation
- Connection verification
- Directory structure setup
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from core.config.settings import settings
from core.config.exceptions import ConfigurationError
from core.database.bootstrap import database_bootstrap, DatabaseBootstrapError
from core.database.connection import db_manager

from core.loggin.logging import setup_logging
logger = setup_logging("system_initializer")

class InitializationError(Exception):
    """Custom exception for initialization failures."""
    pass


class SystemInitializer:
    """
    Orchestrates the system initialization process.

    The initialization follows this sequence:
    1. Validate configuration
    2. Setup logging
    3. Create directories
    4. Bootstrap database (if auto-create enabled)
    5. Create tables
    6. Verify connections
    """

    def __init__(self) -> None:
        """Initialize the system initializer."""
        self._initialized = False
        self.settings = settings

    def validate_configuration(self) -> None:
        """
        Validate critical configuration before proceeding.

        Raises:
            InitializationError: If configuration is invalid
        """
        try:
            # Settings already validates itself on creation
            # But we can add additional checks here

            if self.settings.database_host == "localhost" or self.settings.database_host == "127.0.0.1":
                logger.info("Using local PostgreSQL database")

            # Validate database URL components
            if not all([
                self.settings.database_user,
                self.settings.database_password,
                self.settings.database_name,
                self.settings.database_host,
                self.settings.database_port,
            ]):
                raise ConfigurationError("Incomplete database configuration")

            logger.info("Configuration validation passed")

        except ConfigurationError as e:
            raise InitializationError(f"Configuration validation failed: {e}") from e

    def create_directories(self) -> None:
        """
        Ensure all required directories exist.

        This is idempotent - directories are only created if missing.
        """
        try:
            self.settings.create_required_directories()
            logger.info("Required directories created/verified")
        except Exception as e:
            raise InitializationError(f"Failed to create directories: {e}") from e

    def bootstrap_database(self, create_extensions: bool = False) -> None:
        """
        Bootstrap the database if auto-creation is enabled.

        Args:
            create_extensions: Whether to install optional extensions
        """
        if not self.settings.auto_create_database:
            logger.info("Auto database creation is disabled")
            return

        logger.info("Auto database creation is enabled, bootstrapping...")

        try:
            database_bootstrap.bootstrap(create_extensions=create_extensions)
            logger.info("Database bootstrap completed")
        except DatabaseBootstrapError as e:
            raise InitializationError(f"Database bootstrap failed: {e}") from e

    def create_tables(self, drop_existing: bool = False) -> None:
        """
        Create all application tables.

        Args:
            drop_existing: If True, drop existing tables first (CAUTION!)
        """
        try:
            if drop_existing:
                logger.warning("Dropping existing tables - all data will be lost!")
                confirm = input("Type 'yes' to confirm table deletion: ")
                if confirm.lower() != 'yes':
                    logger.info("Table deletion cancelled")
                    return

            db_manager.create_tables(drop_existing=drop_existing)
            logger.info("Database tables created/verified")

        except Exception as e:
            raise InitializationError(f"Failed to create tables: {e}") from e

    def verify_connections(self) -> None:
        """
        Verify all external connections (database, APIs, etc.).

        This ensures the system can connect to all required services.
        """
        # Verify database connection
        if not db_manager.check_connection():
            raise InitializationError(
                "Cannot connect to database. "
                "Please ensure PostgreSQL is running and credentials are correct."
            )

        logger.info("Database connection verified")

        # Optional: Verify API keys availability
        self._verify_api_keys()

    def _verify_api_keys(self) -> None:
        """Verify that at least one financial data API key is configured."""
        api_keys = [
            ("TWELVEDATA", self.settings.twelvedata_api_key),
            ("POLYGON", self.settings.polygon_api_key),
            ("ALPHAVANTAGE", self.settings.alphavantage_api_key),
        ]

        available_keys = [name for name, key in api_keys if key]

        if not available_keys:
            logger.warning(
                "No financial data API keys configured. "
                "Data ingestion services will not function."
            )
        else:
            logger.info(f"Available API providers: {', '.join(available_keys)}")

    def initialize(
        self,
        bootstrap_db: bool = True,
        create_extensions: bool = False,
        drop_tables: bool = False,
        skip_connection_verify: bool = False,
    ) -> bool:
        """
        Execute the complete system initialization.

        Args:
            bootstrap_db: Whether to bootstrap database (create roles, etc.)
            create_extensions: Whether to install PostgreSQL extensions
            drop_tables: Whether to drop existing tables before creating
            skip_connection_verify: Skip connection verification (for testing)

        Returns:
            bool: True if initialization succeeded

        Raises:
            InitializationError: If initialization fails
        """
        logger.info("=" * 50)
        logger.info("FalconEye System Initialization Starting")
        logger.info("=" * 50)

        try:
            # Phase 1: Validation
            logger.info("Phase 1: Validating configuration...")
            self.validate_configuration()

            # Phase 2: Directory setup
            logger.info("Phase 2: Creating directories...")
            self.create_directories()

            # Phase 3: Database setup
            if bootstrap_db:
                logger.info("Phase 3: Bootstrapping database...")
                self.bootstrap_database(create_extensions=create_extensions)

            # Phase 4: Table creation
            logger.info("Phase 4: Creating tables...")
            self.create_tables(drop_existing=drop_tables)

            # Phase 5: Connection verification
            if not skip_connection_verify:
                logger.info("Phase 5: Verifying connections...")
                self.verify_connections()

            self._initialized = True

            logger.info("=" * 50)
            logger.info("FalconEye System Initialization Completed Successfully")
            logger.info("=" * 50)

            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            logger.error("=" * 50)
            raise InitializationError(f"Initialization failed: {e}") from e

    @property
    def is_initialized(self) -> bool:
        """Check if the system has been successfully initialized."""
        return self._initialized


# Global singleton instance
initializer = SystemInitializer()


def initialize_system(
    bootstrap_db: bool = True,
    create_extensions: bool = False,
    drop_tables: bool = False,
) -> None:
    """
    Convenience function to initialize the system with default settings.

    Args:
        bootstrap_db: Whether to bootstrap database
        create_extensions: Whether to install extensions
        drop_tables: Whether to drop existing tables

    Example:
        from core.startup.initialize import initialize_system

        initialize_system()
        # System is ready to use
    """
    initializer.initialize(
        bootstrap_db=bootstrap_db,
        create_extensions=create_extensions,
        drop_tables=drop_tables,
    )


# Optional: Run initialization when module is imported
# Uncomment if you want auto-initialization on import
# if __name__ != "__main__":
#     try:
#         initialize_system()
#     except InitializationError as e:
#         logger.critical(f"Auto-initialization failed: {e}")
#         sys.exit(1)







# from core.config.settings import settings

# from core.database.bootstrap import (
#     database_bootstrap
# )

# from core.database.connection import (
#     db_manager
# )

# def initialize_system():

#     if settings.auto_create_database:

#         database_bootstrap.bootstrap()

#     db_manager.create_tables()
