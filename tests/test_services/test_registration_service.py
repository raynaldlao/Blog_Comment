from app.services.registration_service import RegistrationService
from tests.factories import make_account


def test_create_account_success(db_session):
    registration_service = RegistrationService(db_session)
    user = registration_service.create_account(
        "new_user", "password123", "new_user@test.com"
    )
    assert isinstance(user, object)
    assert not isinstance(user, str)
    assert user.account_username == "new_user"
    assert user.account_email == "new_user@test.com"
    assert user.account_role == "user"
    assert user.account_id is not None


def test_create_account_username_already_exists(db_session):
    user = make_account(
        account_username="existing_user",
        account_password="password",
        account_email="existing@test.com",
    )
    db_session.add(user)
    db_session.commit()

    registration_service = RegistrationService(db_session)
    result = registration_service.create_account(
        "existing_user", "new_password", "other@test.com"
    )
    assert result == "This username is already taken."


def test_create_account_email_already_exists(db_session):
    user = make_account(
        account_username="user_one",
        account_password="password",
        account_email="taken@test.com",
    )
    db_session.add(user)
    db_session.commit()

    registration_service = RegistrationService(db_session)
    result = registration_service.create_account(
        "user_two", "password", "taken@test.com"
    )
    assert result == "This email is already taken."
