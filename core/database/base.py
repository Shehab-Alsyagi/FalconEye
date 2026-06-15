"""
Base database module that defines the foundational classes and mixins
for all database models in the FalconEye system.

This module provides:
- Declarative base for all models
- Common mixins (timestamps, primary keys, etc.)
- Base configuration for all models
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)
from sqlalchemy.ext.declarative import declared_attr


class Base(DeclarativeBase):
    """
    Base class for all database models in FalconEye.

    Provides common functionality and configuration for all models:
    - Automatic table naming based on class name
    - Consistent schema configuration
    - Type annotation mapping configuration
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.

        Converts CamelCase to snake_case and pluralizes the table name.
        Example: StockPrice -> stock_prices

        Returns:
            str: The generated table name
        """
        import re
        # Convert CamelCase to snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Add 's' for pluralization (simple rule, can be overridden)
        if not name.endswith('s'):
            name += 's'
        return name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update model attributes from dictionary.

        Args:
            data: Dictionary of attributes to update
        """
        for key, value in data.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps to models.

    Features:
    - Automatically sets created_at on insert
    - Automatically updates updated_at on update
    - Uses server time for consistency
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class PrimaryKeyMixin:
    """
    Mixin that adds a primary key 'id' field to models.

    Features:
    - Auto-incrementing integer ID (PostgreSQL SERIAL)
    - Primary key constraint
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the record"
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete capability to models.

    Features:
    - deleted_at timestamp for soft deletion
    - Records are not physically removed from database
    - Queries need to filter out soft-deleted records
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft delete the record by setting deleted_at."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None


class VersionedMixin:
    """
    Mixin that adds optimistic locking version control to models.

    Features:
    - Version counter to prevent concurrent modification conflicts
    - Automatically increments on each update
    """

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Version number for optimistic locking"
    )
