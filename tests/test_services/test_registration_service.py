from app.services.registration_service import RegistrationService
from tests.factories import make_account


def test_create_account_success(db_session):
    registration_service = RegistrationService(db_session)
    user = registration_service.create_account("new_user", "password123")
    assert user is not None
    assert user.account_username == "new_user"
    assert user.account_role == "user"
    assert user.account_id is not None


def test_create_account_already_exists(db_session):
    user = make_account(account_username="existing_user", account_password="password")
    db_session.add(user)
    db_session.commit()

    registration_service = RegistrationService(db_session)
    result = registration_service.create_account("existing_user", "new_password")
    assert result is None
