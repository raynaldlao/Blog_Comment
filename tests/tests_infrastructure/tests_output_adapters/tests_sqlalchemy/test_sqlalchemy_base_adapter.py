from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_exceptions import DatabaseError
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_base_adapter import (
    SqlAlchemyBaseAdapter,
)
from tests.tests_infrastructure.tests_output_adapters.tests_sqlalchemy.sqlalchemy_test_utils import (
    SqlAlchemyTestBase,
)


class _TestAdapter(SqlAlchemyBaseAdapter):
    pass


class TestSqlAlchemyBaseAdapter(SqlAlchemyTestBase):
    @pytest.fixture(autouse=True)
    def setup_adapter(self):
        self.adapter = _TestAdapter(self.session)

    def test_db_get_raises_database_error(self):
        with patch.object(self.adapter._session, "get", side_effect=SQLAlchemyError("mock")):
            with pytest.raises(DatabaseError, match="Database read failed."):
                self.adapter._db_get(object, 1)

    def test_db_add_raises_database_error(self):
        with patch.object(self.adapter._session, "add", side_effect=SQLAlchemyError("mock")):
            with pytest.raises(DatabaseError, match="Database insert failed."):
                self.adapter._db_add(object())

    def test_db_delete_raises_database_error(self):
        with patch.object(self.adapter._session, "delete", side_effect=SQLAlchemyError("mock")):
            with pytest.raises(DatabaseError, match="Database delete failed."):
                self.adapter._db_delete(object())

    def test_db_commit_raises_integrity_error(self):
        with patch.object(self.adapter._session, "commit", side_effect=IntegrityError("mock", "mock", orig=Exception("mock"))):
            with pytest.raises(IntegrityError):
                self.adapter._db_commit()

    def test_db_commit_raises_database_error(self):
        with patch.object(self.adapter._session, "commit", side_effect=SQLAlchemyError("mock")):
            with pytest.raises(DatabaseError, match="Database commit failed."):
                self.adapter._db_commit()

    def test_db_query_raw_raises_database_error(self):
        def _fail():
            raise SQLAlchemyError("mock")

        with pytest.raises(DatabaseError, match="Database query failed."):
            self.adapter._db_query_raw(_fail)
