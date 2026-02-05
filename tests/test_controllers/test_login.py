from tests.factories import make_account


def test_render_login_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<form" in response.data
    assert b'action="/login"' in response.data
    assert b'name="username"' in response.data
    assert b'name="password"' in response.data
    assert b'type="submit"' in response.data

def test_login_authentication_success(client, db_session):
    user = make_account(account_username="test_user", account_password="Hello789")
    db_session.add(user)
    db_session.commit()

    response = client.post("/login", data={
        "username": "test_user",
        "password": "Hello789"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert f"Welcome {user.account_username}".encode() in response.data

def test_login_authentication_failure(client, db_session):
    user = make_account(account_username="wrong_user", account_password="good_password")
    db_session.add(user)
    db_session.commit()

    response = client.post("/login", data={
        "username": "wrong_user",
        "password": "bad_password"
    }, follow_redirects=True)

    assert b"Incorrect username or password." in response.data

def test_login_non_existent_user(client):
    response = client.post("/login", data={
        "username": "ghost",
        "password": "password"
    }, follow_redirects=True)
    assert b"Incorrect username or password." in response.data

def test_login_with_empty_fields(client):
    response = client.post("/login", data={
        "username": "",
        "password": ""
    }, follow_redirects=True)
    assert b"Incorrect username or password." in response.data

def test_login_route_method_protection(client):
    response = client.get("/login")
    assert response.status_code == 405

def test_dashboard_access_denied_without_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert b"Welcome" not in response.data
    assert response.status_code == 200

def test_dashboard_session_persistence(client, db_session):
    user = make_account(account_username="perry", account_password="123")
    db_session.add(user)
    db_session.commit()

    client.post("/login", data={
        "username": "perry",
        "password": "123"
    })

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert f"Welcome {user.account_username}".encode() in response.data

def test_logout(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()

    client.post("/login", data={
        "username": "Xxx__D4RK_V4D0R__xxX",
        "password": "987654321abcdefg@"
    })

    client.get("/logout", follow_redirects=True)

    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "username" not in session
