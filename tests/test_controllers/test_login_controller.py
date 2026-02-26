from tests.factories import make_account


def test_render_login_page(client):
    response = client.get("/login-page")
    assert response.status_code == 200
    assert b'action="/login"' in response.data


def test_login_success(client, db_session):
    user = make_account(account_username="Vador", account_password="dark_password")
    db_session.add(user)
    db_session.commit()
    response = client.post("/login", data={"username": "Vador", "password": "dark_password"}, follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == user.account_id
        assert session["username"] == "Vador"
        assert session["role"] == "user"


def test_logout(client, db_session):
    with client.session_transaction() as session:
        session["user_id"] = 1

    client.get("/logout", follow_redirects=True)

    with client.session_transaction() as session:
        assert "user_id" not in session
