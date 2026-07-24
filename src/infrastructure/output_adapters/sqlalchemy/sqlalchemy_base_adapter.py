from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from blog_exceptions import DatabaseError


class SqlAlchemyBaseAdapter:
    """Base for SQLAlchemy output adapters.

    Wraps common DB operations to translate SQLAlchemyError -> DatabaseError.
    IntegrityError is re-raised for callers that handle unique constraints.
    """

    def __init__(self, session: Session):
        """Initialize with an active SQLAlchemy database session.

        Args:
            session: Active DB session.
        """
        self._session = session

    def _db_get(self, model_class, pk):
        """Get a record by primary key.

        Args:
            model_class: SQLAlchemy model class.
            pk: Primary key value.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        try:
            return self._session.get(model_class, pk)
        # SQLAlchemy library exception — caught and translated to DatabaseError.
        # Not in blog_exceptions.py. Do not move it there.
        except SQLAlchemyError as e:
            raise DatabaseError("Database read failed.") from e

    def _db_add(self, model):
        """Add a model instance to the session.

        Args:
            model: SQLAlchemy model instance.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        try:
            self._session.add(model)
        # SQLAlchemy library exception — caught and translated to DatabaseError.
        # Not in blog_exceptions.py. Do not move it there.
        except SQLAlchemyError as e:
            raise DatabaseError("Database insert failed.") from e

    def _db_delete(self, model):
        """Delete a model instance from the session.

        Args:
            model: SQLAlchemy model instance.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        try:
            self._session.delete(model)
        # SQLAlchemy library exception — caught and translated to DatabaseError.
        # Not in blog_exceptions.py. Do not move it there.
        except SQLAlchemyError as e:
            raise DatabaseError("Database delete failed.") from e

    def _db_commit(self):
        """Commit the current transaction.

        Handles rollback on error. IntegrityError is re-raised so callers
        can handle unique constraint violations with domain exceptions.

        Raises:
            IntegrityError: Re-raised for caller-specific handling.
            DatabaseError: If a non-integrity SQLAlchemy error occurs.
        """
        try:
            self._session.commit()
        # SQLAlchemy library exception — re-raised for constraint handling by callers.
        # Not in blog_exceptions.py. Do not move it there.
        except IntegrityError:
            self._session.rollback()
            raise
        # SQLAlchemy library exception — caught and translated to DatabaseError.
        # Not in blog_exceptions.py. Do not move it there.
        except SQLAlchemyError as e:
            self._session.rollback()
            raise DatabaseError("Database commit failed.") from e

    def _db_query_first(self, model_class, **filters):
        """Query.filter_by(**filters).first() with error wrapping.

        Args:
            model_class: SQLAlchemy model class.
            **filters: Column-value filter pairs.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        return self._db_query_raw(
            lambda: self._session.query(model_class).filter_by(**filters).first()
        )

    def _db_query_all(self, model_class, **filters):
        """Query.filter_by(**filters).all() with error wrapping.

        Args:
            model_class: SQLAlchemy model class.
            **filters: Column-value filter pairs.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        return self._db_query_raw(
            lambda: self._session.query(model_class).filter_by(**filters).all()
        )

    def _db_query_raw(self, query_fn):
        """Execute an arbitrary query function with error wrapping.

        Args:
            query_fn: A callable that performs SQLAlchemy query operations.

        Raises:
            DatabaseError: If a SQLAlchemy error occurs.
        """
        try:
            return query_fn()
        # SQLAlchemy library exception — caught and translated to DatabaseError.
        # Not in blog_exceptions.py. Do not move it there.
        except SQLAlchemyError as e:
            raise DatabaseError("Database query failed.") from e
