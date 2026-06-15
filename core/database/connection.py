"""
Database connection management module for FalconEye.

This module provides:
- Singleton DatabaseManager for connection pooling
- Session lifecycle management
- Connection health checking
- Graceful shutdown handling
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from core.config.settings import settings
from core.database.base import Base
from core.loggin.logging import setup_logging

logger = setup_logging("database_connection")


class DatabaseManager:
    """
    Singleton manager for PostgreSQL database connections using SQLAlchemy.

    Features:
    - Thread-safe connection pooling
    - Automatic retry logic for failed connections
    - Health checking with configurable intervals
    - Graceful connection disposal

    Usage:
        db = DatabaseManager()
        with db.session_scope() as session:
            session.query(User).all()
    """

    _instance: Optional[DatabaseManager] = None
    _initialized: bool = False

    def __new__(cls) -> DatabaseManager:
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize database connection manager (only once)."""
        if self._initialized:
            return

        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
        self._register_events()
        self._initialized = True

    def _initialize_engine(self) -> None:
        """
        Create SQLAlchemy engine with connection pooling.

        Configuration:
        - Pool size and overflow limits
        - Connection recycle time
        - Pre-ping for connection validation
        """
        try:
            self.engine = create_engine(
                settings.database_url,
                echo=settings.db_echo,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=settings.db_pool_pre_ping,
                poolclass=QueuePool,
                future=True,  # Enable SQLAlchemy 2.0 style
                connect_args={
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                },
            )

            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
                class_=Session,
            )

            logger.info(
                f"Database engine initialized: "
                f"{settings.database_host}:{settings.database_port}/"
                f"{settings.database_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def _register_events(self) -> None:
        """Register SQLAlchemy event listeners for debugging and monitoring."""

        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, params, context, executemany
        ):
            """Log SQL queries when debugging is enabled."""
            if settings.db_echo:
                logger.debug(f"SQL Query: {statement}")
                if params:
                    logger.debug(f"Parameters: {params}")

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, params, context, executemany
        ):
            """Log execution time for long-running queries."""
            if settings.db_echo:
                logger.debug(f"Query executed successfully")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session object

        Note:
            Caller is responsible for closing the session.
            Use session_scope context manager for automatic handling.
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")

        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional session scope.

        This context manager automatically handles:
        - Session creation
        - Commit on success
        - Rollback on exception
        - Session closure

        Yields:
            Session: SQLAlchemy session for database operations

        Example:
            with db_manager.session_scope() as session:
                session.add(user)
                session.commit()  # Optional, auto-commits on exit
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
            logger.debug("Session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Session rolled back due to: {e}")
            raise
        finally:
            session.close()
            logger.debug("Session closed")

    @contextmanager
    def readonly_session(self) -> Generator[Session, None, None]:
        """
        Provide a read-only session that never commits.

        Useful for queries that should not modify data.

        Yields:
            Session: Read-only SQLAlchemy session
        """
        session = self.get_session()
        try:
            yield session
        finally:
            session.rollback()  # Ensure no pending transactions
            session.close()

    def check_connection(self, retry_count: int = 3) -> bool:
        """
        Verify database connectivity.

        Args:
            retry_count: Number of retry attempts

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        import time

        for attempt in range(retry_count):
            try:
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                    logger.info("Database connection check successful")
                    return True
            except SQLAlchemyError as e:
                logger.warning(
                    f"Connection check failed (attempt {attempt + 1}/{retry_count}): {e}"
                )
                if attempt < retry_count - 1:
                    time.sleep(1)

        logger.error("Database connection check failed after all retries")
        return False

    def create_tables(self, drop_existing: bool = False) -> None:
        """
        Create all database tables based on SQLAlchemy models.

        Args:
            drop_existing: If True, drops existing tables before creating

        Warning:
            Setting drop_existing=True will delete all data!
        """
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully")

        Base.metadata.create_all(bind=self.engine)
        logger.info("All tables created successfully")

    def dispose(self) -> None:
        """
        Dispose of the database engine and close all connections.

        Should be called during application shutdown.
        """
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed successfully")

    def __enter__(self) -> DatabaseManager:
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure cleanup when used as context manager."""
        self.dispose()


# Global singleton instance
db_manager = DatabaseManager()
