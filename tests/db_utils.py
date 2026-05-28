from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


def truncate_all_tables(session: Session):
    """
    Safely truncates all tables managed by the SqlAlchemyModel registry.
    Uses a single command with CASCADE to avoid deadlocks and handles sequences.
    """
    tables = SqlAlchemyModel.metadata.sorted_tables
    if not tables:
        return

    table_names = ", ".join(f'"{t.name}"' for t in tables)
    session.execute(text("SET lock_timeout = '3s';"))
    session.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))
    session.commit()
