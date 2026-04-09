import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class SqlAlchemyTestBase:
    """
    Shared Base class for SQLAlchemy integration tests (Persistence for Inspection mode).

    Strategy:
        - Orchestrated via the 'db_context' autouse fixture.
        - BEFORE each test: database is cleaned.
        - DURING each test: real commits are allowed.
        - AFTER each test: session is closed, data persists for inspection.
    """

    @staticmethod
    def _truncate_all(connection):
        """Purges all tables and resets sequences. Called before each test."""
        tables = SqlAlchemyModel.metadata.sorted_tables
        table_names = ", ".join(f'"{t.name}"' for t in tables)
        if table_names:
            connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))

    @pytest.fixture(autouse=True)
    def db_context(self, db_engine):
        """
        Pytest fixture that orchestrates the database state for each test.
        Replaces setup_method/teardown_method for better fixture integration.
        """
        with db_engine.begin() as conn:
            self._truncate_all(conn)

        session_factory = sessionmaker(bind=db_engine)
        self.session = session_factory()
        self.engine = db_engine
        yield
        self.session.close()


class AccountDataBuilder:
    """Specialized builder for creating Account records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        username="testuser",
        password="password123",
        email="test@example.com",
        role="user",
    ) -> AccountModel:
        model = AccountModel()
        model.account_username = username
        model.account_password = password
        model.account_email = email
        model.account_role = role
        self._session.add(model)
        self._session.commit()
        return model


class ArticleDataBuilder:
    """Specialized builder for creating Article records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        author_id: int,
        title: str = "Test Title",
        content: str = "Test Content",
        published_at=None,
    ) -> ArticleModel:
        model = ArticleModel()
        model.article_author_id = author_id
        model.article_title = title
        model.article_content = content
        if published_at:
            model.article_published_at = published_at
        self._session.add(model)
        self._session.commit()
        return model


class CommentDataBuilder:
    """Specialized builder for creating Comment records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        article_id: int,
        author_id: int,
        content: str = "Test Comment",
        reply_to: int | None = None,
    ) -> CommentModel:
        model = CommentModel()
        model.comment_article_id = article_id
        model.comment_written_account_id = author_id
        model.comment_reply_to = reply_to
        model.comment_content = content
        self._session.add(model)
        self._session.commit()
        return model
