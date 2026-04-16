import functools

from flask import g as global_request_context

from src.application.input_ports.account_session_management import AccountSessionManagement


class FlaskHandler:
    """
    Orchestrator for Flask global lifecycle hooks and request context.
    Acts as the 'Concierge' to handle cross-cutting concerns like authentication and error handling.
    """

    @staticmethod
    def register_before_request_handler(app, session_service: AccountSessionManagement):
        """
        Registers a global 'before_request' hook.

        FUNCTIONING:
        - Registration: This method is called ONCE during the app bootstrap.
        - Execution: The internal 'identify_user' hook is called by Flask
          AUTOMATICALLY before EVERY SINGLE request.
        - Persistence: It populates the 'global_request_context' (flask.g)
          with the domain Account entity, making identity available
          to all downstream adapters and templates.

        Args:
            app (Flask): The Flask application instance.
            session_service (AccountSessionManagement): The port used to retrieve user data.
        """
        app.before_request(functools.partial(FlaskHandler.identify_user, session_service=session_service))

    @staticmethod
    def identify_user(session_service: AccountSessionManagement):
        """Injects the current user into the global request context."""
        global_request_context.current_user = session_service.get_current_account()
