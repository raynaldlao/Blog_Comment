from datetime import datetime

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel


class TestArticleReading:
    """Grouped tests for core article reading, pagination, and performance."""

    def test_n_plus_one_optimization_integ(self, client, db_session):
        """
        Verifies that batch fetching works correctly against PostgreSQL.
        """
        authors = []
        for i in range(3):
            acc = AccountModel(
                account_username=f"author_{i}",
                account_email=f"author_{i}@test.com",
                account_password="...",
                account_role="author"
            )
            db_session.add(acc)
            authors.append(acc)
        db_session.commit()

        for i, auth in enumerate(authors):
            art = ArticleModel(
                article_title=f"Article {i}",
                article_content=f"Content {i}",
                article_author_id=auth.account_id,
                article_published_at=datetime.now()
            )

            db_session.add(art)

        db_session.commit()
        response = client.get("/")
        assert response.status_code == 200
        for i in range(3):
            assert f"author_{i}".encode() in response.data
            assert f"Article {i}".encode() in response.data

    def test_pagination_actual_pages_integ(self, client, db_session):
        """
        Verifies that the application correctly paginates large volumes of data.
        """
        auth = AccountModel(account_username="paginator", account_email="p@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()

        for i in range(1, 16):
            art = ArticleModel(
                article_title=f"Paged Article {i:02d}",
                article_content="...",
                article_author_id=auth.account_id,
            )
            db_session.add(art)
        db_session.commit()

        response_p1 = client.get("/")
        assert response_p1.status_code == 200
        assert response_p1.data.count(b"Paged Article") == 10
        response_p2 = client.get("/?page=2")
        assert response_p2.status_code == 200
        assert response_p2.data.count(b"Paged Article") == 5

    def test_large_content_and_unicode_integ(self, client, db_session):
        """
        Stress test: Large content and special characters (Emojis, Unicode).
        """
        auth = AccountModel(account_username="unicode_boss", account_email="u@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        large_content = "Word " * 20000
        special_title = "Special 🚀 Title 🌟 - 日本語 - 🛠️"

        art = ArticleModel(
            article_title=special_title,
            article_content=large_content,
            article_author_id=auth.account_id
        )

        db_session.add(art)
        db_session.commit()
        response = client.get(f"/articles/{art.article_id}")
        assert response.status_code == 200
        assert special_title.encode() in response.data
        assert b"Word Word" in response.data

class TestPersistence:
    """Grouped tests for database integrity, cascading deletes, and record fallbacks."""

    def test_cascading_deletes_account_integ(self, client, db_session):
        """
        Verifies that deleting an account removes all its articles and comments.
        """
        auth = AccountModel(account_username="victim", account_email="v@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        art = ArticleModel(article_title="Ghost Article", article_content="...", article_author_id=auth.account_id)
        db_session.add(art)
        db_session.commit()
        cmt = CommentModel(comment_content="My last words", comment_article_id=art.article_id, comment_written_account_id=auth.account_id)
        db_session.add(cmt)
        db_session.commit()
        article_id = art.article_id
        comment_id = cmt.comment_id
        db_session.delete(auth)
        db_session.commit()
        assert db_session.query(ArticleModel).filter_by(article_id=article_id).count() == 0
        assert db_session.query(CommentModel).filter_by(comment_id=comment_id).count() == 0

    def test_orphaned_article_graceful_display_integ(self, client, db_session):
        """
        Verifies that if an article exists without an author, the UI displays fallback info.
        """
        auth = AccountModel(account_username="ghost_writer", account_email="g@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        art = ArticleModel(article_title="Ghost Story", article_content="Once upon a time...", article_author_id=auth.account_id)
        db_session.add(art)
        db_session.commit()
        from unittest.mock import patch
        with patch("src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter.SqlAlchemyAccountAdapter.get_by_id") as mock_get_id:
            with patch("src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter.SqlAlchemyAccountAdapter.get_by_ids") as mock_get_ids:
                mock_get_id.return_value = None
                mock_get_ids.return_value = []
                response = client.get(f"/articles/{art.article_id}")
                assert response.status_code == 200
                assert b"Ghost Story" in response.data
                assert b"Unknown" in response.data or b"identifi" in response.data
