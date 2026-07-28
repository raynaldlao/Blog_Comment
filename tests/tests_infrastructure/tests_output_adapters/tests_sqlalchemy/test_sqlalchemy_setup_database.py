from sqlalchemy import text

from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_setup_database import setup_database


class TestSetupDatabase:
    def test_setup_database_returns_session_when_no_injected_session(self):
        session = setup_database()
        assert session is not None
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        session.close()
        session.remove()  # type: ignore[attr-defined]
