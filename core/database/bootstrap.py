"""
Database bootstrap module for automatic database and role creation.

This module handles:
- PostgreSQL role/user creation
- Database creation
- Permission grants
- Extension setup (e.g., TimescaleDB, pg_stat_statements)
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from core.config.settings import settings
from core.config.exceptions import ConfigurationError
from core.loggin.logging import setup_logging
logger = setup_logging("database_bootstrap")

class DatabaseBootstrapError(Exception):
    """Custom exception for database bootstrap failures."""
    pass


class DatabaseBootstrap:
    """
    Handles bootstrap operations for PostgreSQL database.

    Operations:
    - Ensure application role/user exists
    - Ensure database exists
    - Grant proper privileges
    - Install required extensions

    The bootstrap process is idempotent - it can be run multiple times safely.
    """

    def __init__(self) -> None:
        """Initialize bootstrap with admin connection."""
        self.admin_engine: Optional[Engine] = None
        self._init_admin_engine()

    def _init_admin_engine(self) -> None:
        """
        Create admin engine with superuser privileges for bootstrap operations.

        Uses ADMIN credentials from configuration to perform system-level
        operations like creating users and databases.
        """
        try:
            self.admin_engine = create_engine(
                settings.admin_database_url,
                isolation_level="AUTOCOMMIT",
                future=True,
                pool_size=1,  # Bootstrap should use minimal connections
                connect_args={
                    "connect_timeout": 10,
                },
            )
            logger.info("Admin database engine initialized")
        except Exception as e:
            raise DatabaseBootstrapError(
                f"Failed to create admin database connection: {e}"
            ) from e

    def _execute_admin_query(self, query: str, params: dict = None) -> None:
        """
        Execute a query using admin connection.

        Args:
            query: SQL query to execute
            params: Query parameters for safe execution

        Raises:
            DatabaseBootstrapError: If query execution fails
        """
        if not self.admin_engine:
            raise DatabaseBootstrapError("Admin engine not initialized")

        try:
            with self.admin_engine.connect() as conn:
                conn.execute(text(query), params or {})
                logger.debug(f"Admin query executed: {query[:100]}...")
        except SQLAlchemyError as e:
            raise DatabaseBootstrapError(f"Failed to execute admin query: {e}") from e

    def _role_exists(self, role_name: str) -> bool:
        """
        Check if a PostgreSQL role exists.

        Args:
            role_name: Name of the role to check

        Returns:
            bool: True if role exists, False otherwise
        """
        with self.admin_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_roles
                        WHERE rolname = :role_name
                    )
                """),
                {"role_name": role_name}
            ).scalar()

        return bool(result)

    def ensure_role_exists(self) -> None:
        """
        Create application role if it doesn't exist.

        The role is created with LOGIN permission and the configured password.
        This is idempotent - if the role already exists, no action is taken.
        """
        role_name = settings.database_user

        if self._role_exists(role_name):
            logger.info(f"Role '{role_name}' already exists, skipping creation")
            return

        try:
            # Escape role name if it contains special characters
            safe_role_name = f'"{role_name}"' if '-' in role_name or ' ' in role_name else role_name

            self._execute_admin_query(
                f"""
                CREATE ROLE {safe_role_name}
                WITH LOGIN
                PASSWORD :password
                CREATEDB
                """,
                {"password": settings.database_password}
            )
            logger.info(f"Role '{role_name}' created successfully")
        except DatabaseBootstrapError as e:
            logger.error(f"Failed to create role '{role_name}': {e}")
            raise

    def _database_exists(self, database_name: str) -> bool:
        """
        Check if a database exists.

        Args:
            database_name: Name of the database to check

        Returns:
            bool: True if database exists, False otherwise
        """
        with self.admin_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_database
                        WHERE datname = :db_name
                    )
                """),
                {"db_name": database_name}
            ).scalar()

        return bool(result)

    def ensure_database_exists(self) -> None:
        """
        Create application database if it doesn't exist.

        The database is created with UTF8 encoding and proper owner.
        This is idempotent - if the database already exists, no action is taken.
        """
        database_name = settings.database_name

        if self._database_exists(database_name):
            logger.info(f"Database '{database_name}' already exists, skipping creation")
            return

        try:
            safe_db_name = f'"{database_name}"'
            safe_owner = f'"{settings.database_user}"'

            self._execute_admin_query(
                f"""
                CREATE DATABASE {safe_db_name}
                OWNER {safe_owner}
                ENCODING 'UTF8'
                LC_COLLATE 'en_US.UTF-8'
                LC_CTYPE 'en_US.UTF-8'
                TEMPLATE template0
                """
            )
            logger.info(f"Database '{database_name}' created successfully")
        except DatabaseBootstrapError as e:
            logger.error(f"Failed to create database '{database_name}': {e}")
            raise

    def ensure_permissions(self) -> None:
        """
        Grant all necessary permissions to the application role.

        This includes:
        - Database-level privileges
        - Schema-level privileges (if schema exists)
        """
        database_name = settings.database_name

        try:
            self._execute_admin_query(
                f"""
                GRANT ALL PRIVILEGES
                ON DATABASE "{database_name}"
                TO "{settings.database_user}"
                """
            )
            logger.info(f"Permissions granted on database '{database_name}'")

            # Grant schema permissions (CREATE EXTENSION might need this)
            self._execute_admin_query(
                f"""
                GRANT ALL ON SCHEMA public
                TO "{settings.database_user}"
                """
            )
            logger.debug("Schema permissions granted")

        except DatabaseBootstrapError as e:
            logger.error(f"Failed to grant permissions: {e}")
            raise

    def ensure_extensions(self) -> None:
        """
        Install required PostgreSQL extensions if not already present.

        Common extensions for financial data:
        - timescaledb: For time-series data optimization
        - pg_stat_statements: For query performance monitoring
        """
        extensions = [
            "pg_stat_statements",
            # "timescaledb",  # Uncomment if TimescaleDB is installed
        ]

        # Switch to application database to install extensions
        app_engine = create_engine(
            settings.database_url,
            isolation_level="AUTOCOMMIT",
            future=True,
        )

        try:
            with app_engine.connect() as conn:
                for extension in extensions:
                    try:
                        conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension}"))
                        logger.info(f"Extension '{extension}' ensured")
                    except SQLAlchemyError as e:
                        logger.warning(f"Failed to create extension '{extension}': {e}")
        finally:
            app_engine.dispose()

    def bootstrap(self, create_extensions: bool = False) -> None:
        """
        Execute complete bootstrap process.

        Args:
            create_extensions: Whether to install optional extensions

        The process order is important:
        1. Create role (needed before database creation)
        2. Create database (needs owner role)
        3. Grant permissions (needs database to exist)
        4. Install extensions (optional)
        """
        logger.info("Starting database bootstrap process...")

        try:
            self.ensure_role_exists()
            self.ensure_database_exists()
            self.ensure_permissions()

            if create_extensions:
                self.ensure_extensions()

            logger.info("Database bootstrap completed successfully")

        except DatabaseBootstrapError as e:
            logger.error(f"Database bootstrap failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during bootstrap: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up bootstrap resources."""
        if self.admin_engine:
            self.admin_engine.dispose()
            logger.debug("Admin engine disposed")


# Global singleton instance
database_bootstrap = DatabaseBootstrap()
