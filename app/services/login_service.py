from sqlalchemy import select

from app.models import Account


class LoginService:
    @staticmethod
    def authenticate_user(db_session, username, password):
        query = select(Account).where(Account.account_username == username)
        user = db_session.execute(query).scalar_one_or_none()

        if user and user.account_password == password:
            return user
        return None
