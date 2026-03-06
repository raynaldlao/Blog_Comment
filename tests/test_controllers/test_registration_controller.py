from app.constants import SessionKey
from tests.factories import make_account


def test_render_registration_page(client):
    response = client.get("/registration-page")
    assert response.status_code == 200
    assert b'action="/create-account"' in response.data


def test_create_account_route_success(client, db_session):
    response = client.post("/create-account", data={"username": "new_user", "password": "password"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Account created successfully." in response.data.decode("utf-8")

    with client.session_transaction() as session:
        assert SessionKey.USER_ID not in session


def test_create_account_route_already_exists(client, db_session):
    user = make_account(account_username="existing_user", account_password="password")
    db_session.add(user)
    db_session.commit()
    response = client.post("/create-account", data={"username": "existing_user", "password": "password"}, follow_redirects=True)
    assert response.status_code == 200
    assert b'action="/create-account"' in response.data
    assert "taken" in response.data.decode("utf-8")
