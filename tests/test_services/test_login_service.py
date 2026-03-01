from app.services.login_service import LoginService
from tests.factories import make_account


def test_authenticate_user_success(db_session):
    user = make_account(account_username="leia", account_password="password123")
    db_session.add(user)
    db_session.commit()
    login_service = LoginService(db_session)
    result = login_service.authenticate_user("leia", "password123")
    assert result is not None
    assert result.account_username == "leia"
    assert result.account_role == "user"
    assert result.account_id == user.account_id


def test_authenticate_user_wrong_password(db_session):
    user = make_account(account_username="leia", account_password="password123")
    db_session.add(user)
    db_session.commit()
    login_service = LoginService(db_session)
    result = login_service.authenticate_user("leia", "mauvais_pass")
    assert result is None


def test_authenticate_user_non_existent(db_session):
    login_service = LoginService(db_session)
    result = login_service.authenticate_user("fantome", "rien")
    assert result is None
