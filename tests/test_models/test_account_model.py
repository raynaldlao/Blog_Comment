from datetime import datetime
from typing import cast

import pytest
from sqlalchemy import exc

from app.models.account_model import Account
from tests.factories import make_account


def test_create_account(db_session):
    account = make_account(account_username="Vador")
    db_session.add(account)
    db_session.commit()

    result = db_session.get(Account, account.account_id)
    assert result.account_username == "Vador"
    assert result.account_role == "user"
    assert isinstance(result.account_created_at, datetime)


def test_account_username_unique(db_session):
    db_session.add(make_account(account_username="unique"))
    db_session.commit()

    db_session.add(make_account(account_username="unique"))
    with pytest.raises(exc.IntegrityError):
        db_session.commit()


def test_account_missing_username(db_session):
    # We intentionally pass None to test database constraints
    account = make_account(account_username=cast(str, None))
    db_session.add(account)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()


def test_account_role_invalid(db_session):
    account = make_account(account_role="super_admin")
    db_session.add(account)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()
