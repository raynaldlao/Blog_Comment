from sqlalchemy import select

from app.models.account_model import Account
from database.database_setup import db_session


class LoginService:
    @staticmethod
    def authenticate_user(username, password):
        query = select(Account).where(Account.account_username == username)
        user = db_session.execute(query).scalar_one_or_none()
        if user and user.account_password == password:
            return {
                "id": user.account_id,
                "username": user.account_username,
                "role": user.account_role
            }
        return None
