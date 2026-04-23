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

        create_response = client.post("/articles/new", data={
            "title": article_title,
            "content": article_content
        }, follow_redirects=True)

        assert article_title.encode() in create_response.data
        article_record = db_session.query(ArticleModel).filter_by(article_title=article_title).first()
        article_id = article_record.article_id
        comment_content = "First amazing comment!"

        comment_response = client.post(f"/articles/{article_id}/comments", data={
            "content": comment_content
        }, follow_redirects=True)

        assert comment_content.encode() in comment_response.data
        root_comment = db_session.query(CommentModel).filter_by(comment_content=comment_content).first()
        reply_content = "This is a nested reply!"

        reply_response = client.post(f"/articles/{article_id}/comments/{root_comment.comment_id}/reply", data={
            "content": reply_content
        }, follow_redirects=True)

        assert reply_content.encode() in reply_response.data
        final_view = client.get(f"/articles/{article_id}")
        assert b"tester" in final_view.data
        assert comment_content.encode() in final_view.data
        assert reply_content.encode() in final_view.data

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

        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert b"Level 1" in response.data
        assert b"Level 2" in response.data
        assert b"Level 3" not in response.data
