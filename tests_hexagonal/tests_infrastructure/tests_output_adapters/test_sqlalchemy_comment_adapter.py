# tests_hexagonal/tests_infrastructure/tests_output_adapters/test_sqlalchemy_comment_adapter.py
from src.application.domain.comment import Comment
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter
from tests_hexagonal.tests_infrastructure.tests_output_adapters.sqlalchemy_test_base import SqlAlchemyTestBase


class SqlAlchemyCommentAdapterTestBase(SqlAlchemyTestBase):
    """
    Base class for SqlAlchemyCommentAdapter integration tests.
    """

    def setup_method(self):
        super().setup_method()
        self.repository = SqlAlchemyCommentAdapter(self.session)

    def _insert_account(self) -> AccountModel:
        account = AccountModel()
        account.account_username = "test_author"
        account.account_password = "password123"
        account.account_email = "author@example.com"
        account.account_role = "author"
        self.session.add(account)
        self.session.commit()
        return account

    def _insert_article(
        self,
        author_id: int,
        title: str = "Test Title",
        content: str = "Test Content",
    ) -> ArticleModel:
        model = ArticleModel()
        model.article_author_id = author_id
        model.article_title = title
        model.article_content = content
        self.session.add(model)
        self.session.commit()
        return model

    def _insert_comment(
        self,
        article_id: int,
        author_id: int,
        content: str = "Test Comment",
        reply_to: int | None = None,
    ) -> CommentModel:
        model = CommentModel()
        model.comment_article_id = article_id
        model.comment_written_account_id = author_id
        model.comment_reply_to = reply_to
        model.comment_content = content
        self.session.add(model)
        self.session.commit()
        return model


class TestGetById(SqlAlchemyCommentAdapterTestBase):
    def test_get_by_id_returns_comment(self):
        account = self._insert_account()
        article = self._insert_article(author_id=account.account_id)
        inserted = self._insert_comment(article_id=article.article_id, author_id=account.account_id)
        result = self.repository.get_by_id(inserted.comment_id)
        assert result is not None
        assert isinstance(result, Comment)
        assert result.comment_content == "Test Comment"

    def test_get_by_id_returns_none_if_not_found(self):
        result = self.repository.get_by_id(9999)
        assert result is None


class TestSave(SqlAlchemyCommentAdapterTestBase):
    def test_save_persists_comment_to_database(self):
        account = self._insert_account()
        article = self._insert_article(author_id=account.account_id)

        comment = Comment(
            comment_id=0,
            comment_article_id=article.article_id,
            comment_written_account_id=account.account_id,
            comment_reply_to=None,
            comment_content="My new comment",
            comment_posted_at=None,
        )

        self.repository.save(comment)
        model = self.session.query(CommentModel).filter_by(comment_content="My new comment").first()
        assert model is not None
        assert model.comment_content == "My new comment"
        assert model.comment_article_id == article.article_id
        assert model.comment_written_account_id == account.account_id


class TestDelete(SqlAlchemyCommentAdapterTestBase):
    def test_delete_removes_comment_from_database(self):
        account = self._insert_account()
        article = self._insert_article(author_id=account.account_id)
        inserted = self._insert_comment(article_id=article.article_id, author_id=account.account_id)
        self.repository.delete(inserted.comment_id)
        check = self.repository.get_by_id(inserted.comment_id)
        assert check is None


class TestGetAllByArticleId(SqlAlchemyCommentAdapterTestBase):
    def test_get_all_by_article_id_returns_correct_comments(self):
        account = self._insert_account()
        article1 = self._insert_article(author_id=account.account_id, title="Article 1")
        article2 = self._insert_article(author_id=account.account_id, title="Article 2")
        self._insert_comment(article_id=article1.article_id, author_id=account.account_id, content="Comment 1 for Art 1")
        self._insert_comment(article_id=article1.article_id, author_id=account.account_id, content="Comment 2 for Art 1")
        self._insert_comment(article_id=article2.article_id, author_id=account.account_id, content="Comment 1 for Art 2")
        results = self.repository.get_all_by_article_id(article1.article_id)
        assert len(results) == 2
        assert any(c.comment_content == "Comment 1 for Art 1" for c in results)
        assert any(c.comment_content == "Comment 2 for Art 1" for c in results)
        assert all(c.comment_article_id == article1.article_id for c in results)

    def test_returns_empty_list_when_no_comments(self):
        account = self._insert_account()
        article = self._insert_article(author_id=account.account_id)
        results = self.repository.get_all_by_article_id(article.article_id)
        assert results == []
