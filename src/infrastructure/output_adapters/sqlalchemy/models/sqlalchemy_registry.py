from sqlalchemy.orm import DeclarativeBase


class SqlAlchemyModel(DeclarativeBase):
    """
    Centralized mapper registry for the infrastructure layer.

    This class serves as the shared DeclarativeBase for all SQLAlchemy
    models in the hexagonal architecture, ensuring they reside within
    the same metadata space for relationships and schema creation.
    """
    pass
