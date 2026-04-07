from flask import session as flask_session

from src.application.output_ports.account_session_repository import AccountSessionRepository


class FlaskSessionAdapter(AccountSessionRepository):
    """
    Implementation of the AccountSessionRepository using Flask's internal cookies.

    This adapter translates abstract key-value operations into concrete
    flask.session dictionary manipulations, using only native Python types.
    """

    def store_value(self, key: str, value: str | int | float | bool | dict | list) -> None:
        """
        Assigns a primitive value to a session key using Flask's session object.

        Args:
            key (str): Identifier for the storage key.
            value (str | int | float | bool | dict | list): Data to store in the session.
        """
        flask_session[key] = value

    def retrieve_value(self, key: str) -> str | int | float | bool | dict | list | None:
        """
        Gets a value from a session key using Flask's session object.

        Args:
            key (str): Identifier for the storage key.

        Returns:
            str | int | float | bool | dict | list | None: The stored session data or None if missing.
        """
        return flask_session.get(key)

    def invalidate(self) -> None:
        """
        Wipes the entire Flask session cookie, removing all stored data.
        """
        flask_session.clear()
