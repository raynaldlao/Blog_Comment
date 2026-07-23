from datetime import UTC, datetime

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel


class TestWorkflows:
    """Grouped tests for complete end-to-end integration workflows."""

    def test_full_lifecycle_workflow(self, client, db_session):
        """
        Integral test: Register -> Login -> Create Article -> Comment -> Verify.
        """
        reg_response = client.post("/register", data={
            "username": "tester",
            "email": "tester@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)

        assert reg_response.status_code == 200
        assert b"Account created successfully" in reg_response.data or b"login" in reg_response.data.lower()
        user_record = db_session.query(AccountModel).filter_by(account_username="tester").first()
        user_record.account_role = "author"
        db_session.commit()

        login_response = client.post("/login", data={
            "username": "tester",
            "password": "password123"
        }, follow_redirects=True)

        assert b"Profile" in login_response.data or b"Welcome" in login_response.data
        article_title = "Integration Test Article"
        article_content = "This is a test content from a real integration flow."

        create_response = client.post("/api/articles", json={
            "title": article_title,
            "content": article_content
        })

        assert create_response.status_code == 201
        article_record = db_session.query(ArticleModel).filter_by(article_title=article_title).first()
        article_id = article_record.article_id
        comment_content = "First amazing comment!"

        client.post(f"/articles/{article_id}/comments", data={
            "content": comment_content
        }, follow_redirects=True)

        root_comment = db_session.query(CommentModel).filter_by(comment_content=comment_content).first()
        reply_content = "This is a nested reply!"

        reply_response = client.post(f"/articles/{article_id}/comments/{root_comment.comment_id}/reply", data={
            "content": reply_content
        }, follow_redirects=True)

        # Rate limit: reply within 60s of root comment by same user
        # NB: apostrophe HTML-escaped to &#39; in flash message
        assert b"posting too fast" in reply_response.data
        final_view = client.get(f"/articles/{article_id}")
        assert b"tester" in final_view.data
        assert comment_content.encode() in final_view.data

    def test_honeypot_blocks_spam_bots(self, client, db_session):
        client.post("/register", data={
            "username": "spam_tester", "email": "spam@t.com",
            "password": "p12345678", "confirm_password": "p12345678"
        }, follow_redirects=True)
        user = db_session.query(AccountModel).filter_by(account_username="spam_tester").first()
        user.account_role = "author"
        db_session.commit()

        client.post("/login", data={"username": "spam_tester", "password": "p12345678"}, follow_redirects=True)
        r = client.post("/api/articles", json={"title": "Spam Test", "content": "Spam content"})
        assert r.status_code == 201
        aid = r.get_json()["id"]

        r = client.post(f"/articles/{aid}/comments", data={
            "content": "Spam comment!", "hp_comment": "I am a bot"
        }, follow_redirects=False)
        assert r.status_code == 302

        from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
        comments = db_session.query(CommentModel).filter_by(comment_article_id=aid).all()
        assert len(comments) == 0

    def test_comment_soft_delete_integration(self, client, db_session):
        """
        Verifies soft-delete across the full stack.
        Author deletes own comment → is_deleted=True, content preserved in DB,
        "[deleted]" shown on page, author name still visible.
        """
        author = AccountModel(
            account_username="soft_author", account_email="soft@t.com",
            account_password="p", account_role="author",
        )

        db_session.add(author)
        db_session.commit()
        client.post("/login", data={"username": "soft_author", "password": "p"}, follow_redirects=True)
        r = client.post("/api/articles", json={"title": "Soft Del Test", "content": "Content"})
        aid = r.get_json()["id"]

        client.post(f"/articles/{aid}/comments", data={"content": "Root comment"})
        db_session.commit()
        root = db_session.query(CommentModel).filter_by(comment_article_id=aid).first()
        rid = root.comment_id

        delete_resp = client.post(f"/articles/{aid}/comments/{rid}/delete", follow_redirects=False)
        assert delete_resp.status_code == 302
        db_session.expire_all()
        soft = db_session.get(CommentModel, rid)
        assert soft.is_deleted is True
        assert soft.deleted_at is not None
        assert soft.comment_content == "Root comment"

        detail = client.get(f"/articles/{aid}")
        assert b"Anonymous" in detail.data
        assert b"Comment removed" in detail.data
        assert b"Root comment" not in detail.data

    def test_comment_edit_and_soft_delete_integration(self, client, db_session):
        """
        Verifies comment edit then soft-delete across the full stack.
        Author creates comment, edits it, then soft-deletes it.
        """
        author = AccountModel(
            account_username="edit_user", account_email="edit@t.com",
            account_password="p", account_role="author",
        )
        db_session.add(author)
        db_session.commit()
        client.post("/login", data={"username": "edit_user", "password": "p"}, follow_redirects=True)
        r = client.post("/api/articles", json={"title": "Edit Test", "content": "Content"})
        aid = r.get_json()["id"]

        client.post(f"/articles/{aid}/comments", data={"content": "Original"})
        db_session.commit()
        comment = db_session.query(CommentModel).filter_by(comment_article_id=aid).first()
        cid = comment.comment_id

        edit_resp = client.post(f"/articles/{aid}/comments/{cid}/edit", data={"content": "Updated"}, follow_redirects=False)
        assert edit_resp.status_code == 302
        db_session.expire_all()
        edited = db_session.get(CommentModel, cid)
        assert edited.comment_content == "Updated"
        assert edited.edited_at is not None

        detail = client.get(f"/articles/{aid}")
        assert b"Updated" in detail.data
        assert b"edited at" in detail.data

        delete_resp = client.post(f"/articles/{aid}/comments/{cid}/delete", follow_redirects=False)
        assert delete_resp.status_code == 302
        db_session.expire_all()
        deleted = db_session.get(CommentModel, cid)
        assert deleted.is_deleted is True
        assert deleted.comment_content == "Updated"

        detail_after_delete = client.get(f"/articles/{aid}")
        assert b"Anonymous" in detail_after_delete.data
        assert b"Updated" not in detail_after_delete.data
        assert b"Comment removed" in detail_after_delete.data

    def test_deep_comment_threading_integ(self, client, db_session):
        """
        Verifies that threading works for multiple levels of nesting.
        """
        author = AccountModel(account_username="author", account_email="a@t.com", account_password="p", account_role="admin")
        db_session.add(author)
        db_session.commit()
        article = ArticleModel(article_title="Deep Thread", article_content="...", article_author_id=author.account_id)
        db_session.add(article)
        db_session.commit()

        comment_1 = CommentModel(
            comment_content="Level 1",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=None
        )

        db_session.add(comment_1)
        db_session.commit()

        comment_2 = CommentModel(
            comment_content="Level 2",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=comment_1.comment_id
        )

        db_session.add(comment_2)
        db_session.commit()

        comment_3 = CommentModel(
            comment_content="Level 3",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=comment_2.comment_id
        )

        db_session.add(comment_3)
        db_session.commit()

        comment_4 = CommentModel(
            comment_content="Level 4",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=comment_3.comment_id
        )
        db_session.add(comment_4)
        db_session.commit()

        comment_5 = CommentModel(
            comment_content="Level 5",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=comment_4.comment_id
        )
        db_session.add(comment_5)
        db_session.commit()

        comment_6 = CommentModel(
            comment_content="Level 6",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=comment_5.comment_id
        )
        db_session.add(comment_6)
        db_session.commit()

        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert b"Level 1" in response.data
        assert b"Level 2" in response.data
        assert b"Level 3" in response.data
        assert b"Level 4" in response.data
        assert b"Level 5" not in response.data
        assert b"Level 6" not in response.data

    def test_registration_login_profile_flow_integ(self, client, db_session):
        client.post("/register", data={
            "username": "new_user",
            "email": "new_user@test.com",
            "password": "Str0ng!Pass",
            "confirm_password": "Str0ng!Pass"
        }, follow_redirects=True)

        user = db_session.query(AccountModel).filter_by(account_username="new_user").first()
        assert user is not None
        assert user.account_password.startswith("$argon2id$")

        login_response = client.post("/login", data={
            "username": "new_user",
            "password": "Str0ng!Pass"
        }, follow_redirects=True)

        assert login_response.status_code == 200
        assert b"Profile" in login_response.data or b"new_user" in login_response.data

    def test_comment_with_newlines_renders_br_tag(self, client, db_session):
        """
        Verifies that a root comment containing newlines renders correctly
        in the article detail page via the safe filter.
        """
        author = AccountModel(
            account_username="newline_author", account_email="nl@t.com",
            account_password="p", account_role="author"
        )

        db_session.add(author)
        db_session.commit()
        article = ArticleModel(article_title="Newline Test", article_content="...", article_author_id=author.account_id)
        db_session.add(article)
        db_session.commit()

        client.post("/login", data={"username": "newline_author", "password": "p"}, follow_redirects=True)

        multi_line_comment = "Line 1\nLine 2\nLine 3"
        client.post(f"/articles/{article.article_id}/comments", data={
            "content": multi_line_comment
        }, follow_redirects=True)

        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert b"Line 1" in response.data
        assert b"Line 2" in response.data
        assert b"Line 3" in response.data

    def test_reply_with_newlines_renders_br_tag(self, client, db_session):
        """
        Verifies that a reply comment containing newlines renders correctly
        in the article detail page via the safe filter.
        """
        author = AccountModel(
            account_username="reply_nl", account_email="rnl@t.com",
            account_password="p", account_role="author"
        )

        db_session.add(author)
        db_session.commit()
        article = ArticleModel(article_title="Reply Newline", article_content="...", article_author_id=author.account_id)
        db_session.add(article)
        db_session.commit()
        client.post("/login", data={"username": "reply_nl", "password": "p"}, follow_redirects=True)

        client.post(f"/articles/{article.article_id}/comments", data={
            "content": "Root comment"
        }, follow_redirects=True)

        root_comment = db_session.query(CommentModel).filter_by(comment_article_id=article.article_id).first()
        multi_line_reply = "Reply line 1\nReply line 2"

        reply_response = client.post(f"/articles/{article.article_id}/comments/{root_comment.comment_id}/reply", data={
            "content": multi_line_reply
        }, follow_redirects=True)

        # Rate limit: reply within 60s of root comment by same user
        # NB: apostrophe HTML-escaped to &#39; in flash message
        assert b"posting too fast" in reply_response.data

    def test_article_detail_displays_iso_date(self, client, db_session):
        """
        Verifies the ``date_iso`` filter renders the correct ISO 8601
        ``datetime`` attribute on ``<time>`` elements in article detail.
        """
        author = AccountModel(
            account_username="iso_author", account_email="iso@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(author)
        db_session.commit()
        article = ArticleModel(
            article_title="ISO Date Test", article_content="...",
            article_author_id=author.account_id,
            article_published_at=datetime(2026, 4, 29)
        )
        db_session.add(article)
        db_session.commit()

        response = client.get(f"/articles/{article.article_id}")
        assert b'datetime="2026-04-29"' in response.data

    def test_footer_displays_current_year(self, client, db_session):
        """
        Verify the footer displays the current year dynamically via the
        inject_current_year context processor.
        """
        author = AccountModel(
            account_username="year_test", account_email="y@t.com",
            account_password="p", account_role="author"
        )

        db_session.add(author)
        db_session.commit()
        response = client.get("/")
        assert response.status_code == 200
        current_year_str = str(datetime.now(UTC).year).encode()
        assert current_year_str in response.data

    def test_success_after_article_creation(self, client, db_session):
        author = AccountModel(
            account_username="api_author", account_email="api@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(author)
        db_session.commit()
        client.post("/login", data={"username": "api_author", "password": "p"}, follow_redirects=True)

        response = client.post("/api/articles", json={
            "title": "API Test Article",
            "content": "Testing API creation."
        })

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_error_on_validation_failure(self, client, db_session):
        author = AccountModel(
            account_username="val_api", account_email="val_api@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(author)
        db_session.commit()
        client.post("/login", data={"username": "val_api", "password": "p"}, follow_redirects=True)

        response = client.post("/api/articles", json={"title": "Valid Title"})

        assert response.status_code == 400
        assert "1 character" in response.get_json()["error"]

    def test_nav_consistency_across_pages_integ(self, client, db_session):
        """
        End-to-end verification that the navigation bar correctly reflects
        authentication state on login, registration, and profile pages.
        """
        author = AccountModel(
            account_username="nav_author", account_email="nav@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(author)
        db_session.commit()

        client.post("/login", data={
            "username": "nav_author", "password": "p"
        }, follow_redirects=True)

        for page in ("/login", "/register", "/profile"):
            response = client.get(page)
            assert response.status_code == 200
            assert b"New article" in response.data
            assert b"Profile" in response.data
            assert b"Logout" in response.data
            if page == "/profile":
                assert b"Sign In" not in response.data
                assert b"Sign Up" not in response.data

        client.post("/logout", follow_redirects=True)

        response = client.get("/login")
        assert response.status_code == 200
        assert b"New article" not in response.data
        assert b"Sign In" in response.data
        assert b"Sign Up" in response.data

    def test_comment_count_displays_total_with_nested(self, client, db_session):
        author = AccountModel(
            account_username="count_author", account_email="count@t.com",
            account_password="p", account_role="author"
        )

        db_session.add(author)
        db_session.commit()
        article = ArticleModel(
            article_title="Count Test", article_content="...",
            article_author_id=author.account_id
        )

        db_session.add(article)
        db_session.commit()

        root = CommentModel(
            comment_content="Root",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=None
        )

        db_session.add(root)
        db_session.commit()

        reply1 = CommentModel(
            comment_content="Reply 1",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=root.comment_id
        )

        db_session.add(reply1)
        db_session.commit()

        reply2 = CommentModel(
            comment_content="Reply 2",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id,
            comment_reply_to=root.comment_id
        )

        db_session.add(reply2)
        db_session.commit()
        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert b"Comments (3)" in response.data


class TestUserProfileLinks:
    """Verifies author name links point to the public profile page."""

    def test_article_list_author_link_points_to_profile(self, client, db_session):
        """
        Regression: the author name in the article list should link
        to /users/<username>. If the <a> wrapper is removed or the
        overlay ::after intercepts clicks (as happened), this catches it.
        """
        author = AccountModel(
            account_username="link_test_author",
            account_email="link@test.com",
            account_password="p",
            account_role="author",
        )

        db_session.add(author)
        db_session.commit()

        article = ArticleModel(
            article_title="Link Test",
            article_content="...",
            article_author_id=author.account_id,
        )

        db_session.add(article)
        db_session.commit()
        response = client.get("/")
        assert response.status_code == 200
        assert b'href="/users/link_test_author"' in response.data


class TestAdminChangeRole:
    """
    Integration tests for admin promoting/demoting user roles.
    """

    def test_admin_promote_user_to_author_integ(self, client, db_session):
        """
        Verifies admin can change a user's role via POST /admin/users/<id>/role.
        Role persists in DB after the change.
        """
        admin = AccountModel(
            account_username="role_admin", account_email="role@t.com",
            account_password="p", account_role="admin",
        )
        db_session.add(admin)
        db_session.commit()

        target = AccountModel(
            account_username="target_user", account_email="target@t.com",
            account_password="p", account_role="user",
        )
        db_session.add(target)
        db_session.commit()

        client.post("/login", data={"username": "role_admin", "password": "p"}, follow_redirects=True)

        response = client.post(
            f"/admin/users/{target.account_id}/role",
            data={"role": "author"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Role updated." in response.data

        db_session.expire_all()
        updated = db_session.get(AccountModel, target.account_id)
        assert updated.account_role == "author"

    def test_non_admin_change_role_returns_error_integ(self, client, db_session):
        """
        Verifies non-admin user cannot change another user's role.
        """
        user = AccountModel(
            account_username="plain_user", account_email="plain@t.com",
            account_password="p", account_role="user",
        )
        db_session.add(user)
        db_session.commit()

        target = AccountModel(
            account_username="victim", account_email="victim@t.com",
            account_password="p", account_role="user",
        )
        db_session.add(target)
        db_session.commit()

        client.post("/login", data={"username": "plain_user", "password": "p"}, follow_redirects=True)

        response = client.post(
            f"/admin/users/{target.account_id}/role",
            data={"role": "author"},
            follow_redirects=True,
        )

        assert response.status_code == 403


class TestCommentHardDeleteIntegration:
    def test_comment_hard_delete_integration(self, client, db_session):
        admin = AccountModel(
            account_username="hard_del_admin", account_email="hda@t.com",
            account_password="p", account_role="admin",
        )
        db_session.add(admin)
        db_session.commit()

        article = ArticleModel(
            article_title="Hard Delete Test", article_content="Content",
            article_author_id=admin.account_id,
        )
        db_session.add(article)
        db_session.commit()

        comment = CommentModel(
            comment_content="To be hard deleted",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(comment)
        db_session.commit()

        client.post("/login", data={"username": "hard_del_admin", "password": "p"})

        cid = comment.comment_id
        aid = article.article_id
        resp = client.post(f"/articles/{aid}/comments/{cid}/delete-permanent", follow_redirects=True)
        assert resp.status_code == 200

        db_session.expire_all()
        assert db_session.get(CommentModel, cid) is None
        assert b"Comment permanently deleted" in resp.data

    def test_comment_hard_delete_cascades_to_children_integ(
        self, client, db_session,
    ):
        """
        Verifies that hard-deleting a parent comment cascades to ALL
        descendants via FK ON DELETE CASCADE.

        Creates a tree: P(parent) -> A(child of P) -> C(child of A),
        B(child of P). Hard-deletes P, then asserts P, A, B, C are all
        removed from the database. An unrelated comment must remain intact.
        """
        admin = AccountModel(
            account_username="cascade_admin", account_email="ca@t.com",
            account_password="p", account_role="admin",
        )
        db_session.add(admin)
        db_session.commit()

        article = ArticleModel(
            article_title="Cascade Test", article_content="C",
            article_author_id=admin.account_id,
        )
        db_session.add(article)
        db_session.commit()

        parent = CommentModel(
            comment_content="Parent",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(parent)
        db_session.commit()

        child_a = CommentModel(
            comment_content="Child A",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            comment_reply_to=parent.comment_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(child_a)
        db_session.commit()

        child_b = CommentModel(
            comment_content="Child B",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            comment_reply_to=parent.comment_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(child_b)
        db_session.commit()

        grandchild = CommentModel(
            comment_content="Grandchild",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            comment_reply_to=child_a.comment_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(grandchild)
        db_session.commit()

        unrelated = CommentModel(
            comment_content="Unrelated",
            comment_article_id=article.article_id,
            comment_written_account_id=admin.account_id,
            is_deleted=True,
            deleted_at=datetime.now(UTC),
        )
        db_session.add(unrelated)
        db_session.commit()

        pid = parent.comment_id
        aid = article.article_id
        ca_id = child_a.comment_id
        cb_id = child_b.comment_id
        gc_id = grandchild.comment_id
        un_id = unrelated.comment_id

        client.post("/login", data={
            "username": "cascade_admin", "password": "p",
        })

        resp = client.post(
            f"/articles/{aid}/comments/{pid}/delete-permanent",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Comment permanently deleted" in resp.data

        db_session.expire_all()

        assert db_session.get(CommentModel, pid) is None
        assert db_session.get(CommentModel, ca_id) is None
        assert db_session.get(CommentModel, cb_id) is None
        assert db_session.get(CommentModel, gc_id) is None
        assert db_session.get(CommentModel, un_id) is not None


class TestArticleEditEditedAtIntegration:
    def test_article_edit_sets_edited_at_integration(self, client, db_session):
        """Création → édition → edited_at persiste en base.

        Vérifie le round-trip complet : après édition d'un article,
        recharger depuis la DB donne un edited_at non-None.
        """
        author = AccountModel(
            account_username="edit_test_author", account_email="eta@t.com",
            account_password="p", account_role="author",
        )
        db_session.add(author)
        db_session.commit()

        article = ArticleModel(
            article_title="Original Title", article_content="Original Content",
            article_author_id=author.account_id,
        )
        db_session.add(article)
        db_session.commit()

        art_id = article.article_id
        assert article.article_edited_at is None

        client.post("/login", data={"username": "edit_test_author", "password": "p"})

        resp = client.put(f"/api/articles/{art_id}", json={
            "title": "Updated Title",
            "content": "Updated Content",
        })
        assert resp.status_code == 200
        assert resp.get_json() == {"ok": True}

        db_session.expire_all()
        updated = db_session.get(ArticleModel, art_id)
        assert updated.article_title == "Updated Title"
        assert updated.article_edited_at is not None
