from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_uploaded_file_model import UploadedFileModel


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
        response_1 = client.get("/")
        assert b"old_name" in response_1.data
        response_2 = client.get(f"/articles/{art.article_id}")
        assert b"old_name" in response_2.data
        auth.account_username = "new_legend"
        db_session.commit()
        response_3 = client.get("/")
        assert b"new_legend" in response_3.data
        assert b"old_name" not in response_3.data


class TestProfilePhoto:
    """Tests for profile photo upload, replace, and remove via DB."""

    OLD_FILE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    def _create_user_and_old_file(self, db_session):
        old_file = UploadedFileModel(
            file_id=self.OLD_FILE_ID,
            original_filename="old_avatar.jpg",
            mime_type="image/jpeg",
            file_size=100,
            file_data=b"old-image-data",
        )
        db_session.add(old_file)
        auth = AccountModel(
            account_username="photo_user",
            account_email="photo@test.com",
            account_password="p",
            account_role="user",
            avatar_file_id=self.OLD_FILE_ID,
        )
        db_session.add(auth)
        db_session.commit()
        return auth

    def test_upload_replaces_old_avatar_and_remove_clears_integ(self, client, db_session):
        auth = self._create_user_and_old_file(db_session)
        client.post("/login", data={"username": "photo_user", "password": "p"}, follow_redirects=True)

        upload_resp = client.post(
            "/api/profile/photo",
            data={"file": (BytesIO(b"new-image-data"), "new_avatar.jpg", "image/jpeg")},
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 200
        body = upload_resp.get_json()
        assert body is not None
        new_file_id = body["avatar_url"].split("/")[2]

        db_session.expire_all()
        updated_account = db_session.query(AccountModel).filter_by(account_id=auth.account_id).first()
        assert updated_account.avatar_file_id == new_file_id
        old_file = db_session.query(UploadedFileModel).filter_by(file_id=self.OLD_FILE_ID).first()
        assert old_file is None

        remove_resp = client.post("/profile/photo/delete", follow_redirects=True)
        assert remove_resp.status_code == 200
        assert b"Profile photo removed." in remove_resp.data

        db_session.expire_all()
        updated_account = db_session.query(AccountModel).filter_by(account_id=auth.account_id).first()
        assert updated_account.avatar_file_id is None
        deleted_new_file = db_session.query(UploadedFileModel).filter_by(file_id=new_file_id).first()
        assert deleted_new_file is None


class TestEmailUpdate:
    """Tests for account email change flow via the full Flask stack."""

    def test_update_email_flow(self, client, db_session):
        auth = AccountModel(
            account_username="email_user",
            account_email="before@test.com",
            account_password="p",
            account_role="user",
        )
        db_session.add(auth)
        db_session.commit()

        client.post("/login", data={"username": "email_user", "password": "p"}, follow_redirects=True)

        response = client.post("/profile/email", data={"email": "after@test.com"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Email updated." in response.data

        profile = client.get("/profile")
        assert b"after@test.com" in profile.data
        assert b"before@test.com" not in profile.data


class TestPasswordUpdate:
    """Tests for account password change flow via the full Flask stack."""

    def test_update_password_flow(self, client, db_session):
        auth = AccountModel(
            account_username="pass_user",
            account_email="pass@test.com",
            account_password="old_pass",
            account_role="user",
        )
        db_session.add(auth)
        db_session.commit()

        client.post("/login", data={"username": "pass_user", "password": "old_pass"}, follow_redirects=True)

        response = client.post("/profile/password", data={"new_password": "new_pass"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Password updated." in response.data

        client.post("/logout", follow_redirects=True)
        login = client.post("/login", data={"username": "pass_user", "password": "new_pass"}, follow_redirects=True)
        assert b"Profile" in login.data


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


class TestAdminUserList:
    """Tests for admin user list with pagination."""

    def test_admin_user_list_pagination(self, client, db_session):
        for i in range(25):
            db_session.add(AccountModel(
                account_username=f"user_{i}",
                account_email=f"user_{i}@test.com",
                account_password="p",
                account_role="user"
            ))
        admin = AccountModel(
            account_username="admin_user",
            account_email="admin@test.com",
            account_password="admin_pass",
            account_role="admin"
        )
        db_session.add(admin)
        db_session.commit()

        client.post("/login", data={"username": "admin_user", "password": "admin_pass"}, follow_redirects=True)

        r1 = client.get("/admin/users")
        assert r1.status_code == 200
        assert b"user_0" in r1.data
        assert b"user_19" in r1.data
        assert b"user_20" not in r1.data
        assert b"page-link-num" in r1.data

        r2 = client.get("/admin/users?page=2")
        assert r2.status_code == 200
        assert b"user_20" in r2.data
        assert b"user_24" in r2.data
        assert b"user_0" not in r2.data
        assert b"page-link-num" in r2.data
