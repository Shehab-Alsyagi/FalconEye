from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy import text

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session
)

from sqlalchemy.exc import SQLAlchemyError

from core.config.settings import settings

Base = declarative_base()

class DatabaseManager:
    """ Manages the database connection using SQLAlchemy, providing a session factory and context manager for safe session handling.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.engine = self._create_engine()

        self.SessionLocal = self._create_session_factory()
        self._initialized = True


    def _create_engine(self):
        return create_engine(
            settings.database_url,
            echo= settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=settings.db_pool_pre_ping,

            # why !? : for SQLAlchemy 2.0 style usage, see: https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html#change-2.0-usage-of-create-engine-and-sessionmaker
            future=True
        )


    def _create_session_factory(self):
        return sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_ = Session
        )

    def get_session(self) -> Session:
        """ Provides a transactional scope around a series of operations. """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """ Provides a transactional scope around a series of operations. """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


    def check_connection(self) -> bool:
        """ Checks if the database connection is successful. """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def create_tables(self):
        """ Creates all tables defined in the SQLAlchemy models. """
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """ Drops all tables defined in the SQLAlchemy models. """
        Base.metadata.drop_all(bind=self.engine)

    # def dispose(self):
    #     """ Disposes of the database engine, closing all connections. """
    #     self.engine.dispose()

    # def __del__(self):
    #     """ Ensures that the database engine is properly disposed of when the instance is destroyed. """
    #     self.dispose()

db_manager = DatabaseManager()

