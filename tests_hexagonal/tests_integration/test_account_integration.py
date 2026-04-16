from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel


class TestRegistration:
    """Grouped tests for account creation and registration business rules."""

    def test_duplicate_registration_handling_integ(self, client, db_session):
        """
        Verifies that the app handles duplicate usernames/emails at the integration level.
        """
        existing = AccountModel(
            account_username="existing_user",
            account_email="existing@test.com",
            account_password="password",
            account_role="user"
        )

        db_session.add(existing)
        db_session.commit()

        response_uname = client.post("/register", data={
            "username": "existing_user",
            "email": "new@test.com",
            "password": "password",
            "confirm_password": "password"
        }, follow_redirects=True)

        assert b"already taken" in response_uname.data.lower()

        response_email = client.post("/register", data={
            "username": "new_user",
            "email": "existing@test.com",
            "password": "password",
            "confirm_password": "password"
        }, follow_redirects=True)

        assert b"already taken" in response_email.data.lower()

class TestProfile:
    """Grouped tests for profile management and session persistence."""

    def test_profile_update_propagation_and_session_integ(self, client, db_session):
        """
        Verifies session persistence and that name changes propagate to all views.
        """
        auth = AccountModel(
            account_username="old_name",
            account_email="old@test.com",
            account_password="p",
            account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        art = ArticleModel(article_title="My Bio", article_content="...", article_author_id=auth.account_id)
        db_session.add(art)
        db_session.commit()
        client.post("/login", data={"username": "old_name", "password": "p"}, follow_redirects=True)
        res1 = client.get("/")
        assert b"old_name" in res1.data
        res2 = client.get(f"/articles/{art.article_id}")
        assert b"old_name" in res2.data
        auth.account_username = "new_legend"
        db_session.commit()
        res3 = client.get("/")
        assert b"new_legend" in res3.data
        assert b"old_name" not in res3.data

class TestConcurrency:
    """Grouped tests for high-concurrency race condition scenarios."""

    @staticmethod
    def _register_worker(client, db_session, data):
        """Dedicated worker for concurrent registration attempts."""
        try:
            return client.post("/register", data=data, follow_redirects=True)
        finally:
            db_session.remove()

    def test_concurrency_race_condition_registration_integ(self, client, db_session):
        """
        Simulates a race condition where multiple identical registration
        requests are sent concurrently.
        """
        registration_data = {
            "username": "race_winner",
            "email": "race@test.com",
            "password": "password123",
            "confirm_password": "password123"
        }

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._register_worker, client, db_session, registration_data)
                for _ in range(5)
            ]
            results = [f.result() for f in futures]

        count = db_session.query(AccountModel).filter_by(account_email="race@test.com").count()
        assert count == 1
        success_count = 0
        for _, r in enumerate(results):
            is_success = r.status_code in [200, 302] and b"already taken" not in r.data.lower()
            if is_success:
                success_count += 1

        assert success_count == 1
