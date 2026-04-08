from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter
from tests_hexagonal.test_domain_factories import create_test_comment
from tests_hexagonal.tests_infrastructure.tests_output_adapters.infrastructure_test_utils import (
    AccountDataBuilder,
    ArticleDataBuilder,
    CommentDataBuilder,
    SqlAlchemyTestBase,
)


class SqlAlchemyCommentAdapterTestBase(SqlAlchemyTestBase):
    def setup_method(self):
        super().setup_method()
        self.repository = SqlAlchemyCommentAdapter(self.session)
        self.account_builder = AccountDataBuilder(self.session)
        self.article_builder = ArticleDataBuilder(self.session)
        self.comment_builder = CommentDataBuilder(self.session)


class TestCommentGetById(SqlAlchemyCommentAdapterTestBase):
    def test_get_by_id_returns_comment(self):
        account = self.account_builder.create()
        article = self.article_builder.create(author_id=account.account_id)
        inserted = self.comment_builder.create(article_id=article.article_id, author_id=account.account_id)
        result = self.repository.get_by_id(inserted.comment_id)
        assert result is not None
        from src.application.domain.comment import Comment
        assert isinstance(result, Comment)
        assert result.comment_content == "Test Comment"

    def test_get_by_id_returns_none_if_not_found(self):
        result = self.repository.get_by_id(9999)
        assert result is None


class TestCommentSave(SqlAlchemyCommentAdapterTestBase):
    def test_save_persists_comment_to_database(self):
        account = self.account_builder.create()
        article = self.article_builder.create(author_id=account.account_id)

        comment = create_test_comment(
            comment_id=0,
            comment_article_id=article.article_id,
            comment_written_account_id=account.account_id,
            comment_reply_to=None,
            comment_content="My new comment",
        )

        self.repository.save(comment)
        model = self.session.query(CommentModel).filter_by(comment_content="My new comment").first()
        assert model is not None
        assert model.comment_content == "My new comment"
        assert model.comment_article_id == article.article_id
        assert model.comment_written_account_id == account.account_id


class TestCommentDelete(SqlAlchemyCommentAdapterTestBase):
    def test_delete_removes_comment_from_database(self):
        account = self.account_builder.create()
        article = self.article_builder.create(author_id=account.account_id)
        inserted = self.comment_builder.create(article_id=article.article_id, author_id=account.account_id)
        self.repository.delete(inserted.comment_id)
        check = self.repository.get_by_id(inserted.comment_id)
        assert check is None


class TestCommentGetAllByArticleId(SqlAlchemyCommentAdapterTestBase):
    def test_get_all_by_article_id_returns_correct_comments(self):
        account = self.account_builder.create()
        article1 = self.article_builder.create(author_id=account.account_id, title="Article 1")
        article2 = self.article_builder.create(author_id=account.account_id, title="Article 2")
        self.comment_builder.create(article_id=article1.article_id, author_id=account.account_id, content="Comment 1 for Art 1")
        self.comment_builder.create(article_id=article1.article_id, author_id=account.account_id, content="Comment 2 for Art 1")
        self.comment_builder.create(article_id=article2.article_id, author_id=account.account_id, content="Comment 1 for Art 2")
        results = self.repository.get_all_by_article_id(article1.article_id)
        assert len(results) == 2
        assert any(c.comment_content == "Comment 1 for Art 1" for c in results)
        assert any(c.comment_content == "Comment 2 for Art 1" for c in results)
        assert all(c.comment_article_id == article1.article_id for c in results)

    def test_returns_empty_list_when_no_comments(self):
        account = self.account_builder.create()
        article = self.article_builder.create(author_id=account.account_id)
        results = self.repository.get_all_by_article_id(article.article_id)
        assert results == []
