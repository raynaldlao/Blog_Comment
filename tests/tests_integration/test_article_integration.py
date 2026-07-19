
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
        Verifies that deleting an account sets FK columns to NULL:
        article_author_id and comment_written_account_id become NULL.
        The comment content is NOT masked here because the test bypasses
        the service layer (masking happens in AccountSessionAdapter).
        """
        auth = AccountModel(account_username="victim", account_email="v@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        art = ArticleModel(article_title="Ghost Article", article_content="...", article_author_id=auth.account_id)
        db_session.add(art)
        db_session.commit()

        cmt = CommentModel(
            comment_content="My last words",
            comment_article_id=art.article_id,
            comment_written_account_id=auth.account_id
        )

        db_session.add(cmt)
        db_session.commit()
        article_id = art.article_id
        comment_id = cmt.comment_id
        db_session.delete(auth)
        db_session.commit()
        assert db_session.query(ArticleModel).filter_by(article_id=article_id).count() == 1
        orphan = db_session.query(ArticleModel).filter_by(article_id=article_id).first()
        assert orphan.article_author_id is None
        orphan_cmt = db_session.query(CommentModel).filter_by(comment_id=comment_id).first()
        assert orphan_cmt is not None
        assert orphan_cmt.comment_written_account_id is None
        assert orphan_cmt.comment_content == "My last words"

    def test_orphan_comment_hard_delete_single_click_integ(self, client, db_session):
        """
        Verifies that an orphaned comment (author deleted) is hard-deleted
        in a single click via the full Flask endpoint pipeline.
        """
        author = AccountModel(
            account_username="orphan_author", account_email="orphan@t.com",
            account_password="p", account_role="author"
        )

        db_session.add(author)
        db_session.commit()

        article = ArticleModel(
            article_title="Orphan Test", article_content="...",
            article_author_id=author.account_id
        )

        db_session.add(article)
        db_session.commit()

        comment = CommentModel(
            comment_content="I will be orphaned",
            comment_article_id=article.article_id,
            comment_written_account_id=author.account_id
        )

        db_session.add(comment)
        db_session.commit()
        comment_id = comment.comment_id
        article_id = article.article_id

        admin = AccountModel(
            account_username="admin_orphan", account_email="admin_o@t.com",
            account_password="p", account_role="admin"
        )

        db_session.add(admin)
        db_session.commit()
        client.post("/login", data={"username": "admin_orphan", "password": "p"}, follow_redirects=True)
        resp = client.post("/account/delete", data={"account_id": author.account_id}, follow_redirects=True)
        assert resp.status_code == 200
        db_session.expire_all()
        orphan = db_session.get(CommentModel, comment_id)
        assert orphan is not None
        assert orphan.comment_written_account_id is None
        assert "<!--cmt-removed-->" in orphan.comment_content

        resp = client.post(
            f"/articles/{article_id}/comments/{comment_id}/delete",
            follow_redirects=False,
        )

        assert resp.status_code == 302
        db_session.expire_all()
        assert db_session.get(CommentModel, comment_id) is None

    def test_article_delete_end_to_end_integ(self, client, db_session):
        """
        Verifies the full article delete flow via POST HTML form.
        Creates an article, logs in, deletes it, and confirms it's gone.
        """
        author = AccountModel(
            account_username="del_author", account_email="del@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(author)
        db_session.commit()

        article = ArticleModel(
            article_title="To Delete", article_content="...",
            article_author_id=author.account_id
        )
        db_session.add(article)
        db_session.commit()
        article_id = article.article_id

        client.post("/login", data={
            "username": "del_author", "password": "p"
        }, follow_redirects=True)

        response = client.post(
            f"/articles/{article_id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Article deleted successfully" in response.data
        assert db_session.query(ArticleModel).filter_by(
            article_id=article_id
        ).count() == 0

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
        target_id = "src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter.SqlAlchemyAccountAdapter.get_by_id"

        target_ids = (
            "src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter"
            ".SqlAlchemyAccountAdapter.get_by_ids"
        )

        with patch(target_id) as mock_get_id:
            with patch(target_ids) as mock_get_ids:
                mock_get_id.return_value = None
                mock_get_ids.return_value = []
                response = client.get(f"/articles/{art.article_id}")
                assert response.status_code == 200
                assert b"Ghost Story" in response.data
                assert b"Unknown" in response.data or b"identifi" in response.data


class TestArticleDescription:
    """Tests for the article description field."""

    def test_create_article_with_description_integ(self, client, db_session):
        auth = AccountModel(
            account_username="desc_author", account_email="desc@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "desc_author", "password": "p"},
                    follow_redirects=True)

        resp = client.post("/api/articles", json={
            "title": "Desc Test",
            "description": "A short description",
            "content": "Article body"
        })
        assert resp.status_code == 201
        article_id = resp.get_json()["id"]

        api_resp = client.get(f"/api/articles/{article_id}")
        assert api_resp.status_code == 200
        data = api_resp.get_json()
        assert data["description"] == "A short description"

    def test_create_article_without_description_integ(self, client, db_session):
        auth = AccountModel(
            account_username="no_desc", account_email="nd@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "no_desc", "password": "p"},
                    follow_redirects=True)

        resp = client.post("/api/articles", json={
            "title": "No Desc",
            "description": "",
            "content": "Article body"
        })
        assert resp.status_code == 201
        article_id = resp.get_json()["id"]

        api_resp = client.get(f"/api/articles/{article_id}")
        data = api_resp.get_json()
        assert data["description"] == ""

    def test_description_shown_in_detail_template(self, client, db_session):
        auth = AccountModel(
            account_username="desc_detail", account_email="dd@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "desc_detail", "password": "p"},
                    follow_redirects=True)

        resp = client.post("/api/articles", json={
            "title": "Detail Desc",
            "description": "Visible in detail",
            "content": "Content"
        })
        article_id = resp.get_json()["id"]

        detail_resp = client.get(f"/articles/{article_id}")
        assert detail_resp.status_code == 200
        assert b"Visible in detail" in detail_resp.data

    def test_update_article_description(self, client, db_session):
        auth = AccountModel(
            account_username="update_desc", account_email="ud@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "update_desc", "password": "p"},
                    follow_redirects=True)

        create_resp = client.post("/api/articles", json={
            "title": "Update Desc", "description": "Old desc", "content": "Body"
        })
        article_id = create_resp.get_json()["id"]

        put_resp = client.put(f"/api/articles/{article_id}", json={
            "title": "Update Desc", "description": "New desc", "content": "Body"
        })
        assert put_resp.status_code == 200

        get_resp = client.get(f"/api/articles/{article_id}")
        assert get_resp.get_json()["description"] == "New desc"

    def test_description_shown_in_list_template(self, client, db_session):
        auth = AccountModel(
            account_username="desc_list", account_email="dl@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "desc_list", "password": "p"},
                    follow_redirects=True)

        client.post("/api/articles", json={
            "title": "List Desc", "description": "Seen in list", "content": "Body"
        })

        list_resp = client.get("/")
        assert list_resp.status_code == 200
        assert b"Seen in list" in list_resp.data


class TestArticleSearch:
    def test_search_by_author_via_list_endpoint(self, client, db_session):
        auth = AccountModel(
            account_username="searchable_author",
            account_email="sa@test.com",
            account_password="p",
            account_role="author",
        )
        db_session.add(auth)
        db_session.commit()

        art = ArticleModel(
            article_title="Author Search Test",
            article_content="Content",
            article_author_id=auth.account_id,
        )
        db_session.add(art)
        db_session.commit()

        resp = client.get("/?q=searchable")
        assert resp.status_code == 200
        assert b"Author Search Test" in resp.data

        resp_no_match = client.get("/?q=nonexistentuser")
        assert resp_no_match.status_code == 200
        assert b"No articles" in resp_no_match.data
