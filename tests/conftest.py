import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base  # Assure-toi que Base est bien défini dans app/models.py

# Configuration de la base de test
DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_blog_db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Réinitialisation de la base une seule fois au début de la session Pytest
@pytest.fixture(scope="session", autouse=True)
def reset_database():
    print("\n🔄 Réinitialisation de la base test_blog_db...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Base test_blog_db nettoyée.")

# Session de base de données pour chaque test
@pytest.fixture(scope="function")
def db_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
