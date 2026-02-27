from tests.factories import make_account


def test_render_login_page(client):
    response = client.get("/login-page")
    assert response.status_code == 200
    assert b'action="/login"' in response.data

def test_login_method_not_allowed(client):
    response = client.get("/login")
    assert response.status_code == 405

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

def test_login_failure_wrong_password(client, db_session):
    user = make_account(account_username="Luke", account_password="correct_password")
    db_session.add(user)
    db_session.commit()
    response = client.post("/login", data={"username": "Luke", "password": "wrong_password"}, follow_redirects=True)
    assert b"Incorrect credentials." in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session

def test_login_non_existent_user(client):
    response = client.post("/login", data={"username": "Inconnu", "password": "password"}, follow_redirects=True)
    assert b"Incorrect credentials." in response.data

def test_logout(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["username"] = "Test"
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "username" not in session
