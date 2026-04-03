from src.application.domain.article import Article
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from tests_hexagonal.tests_infrastructure.tests_output_adapters.sqlalchemy_test_base import SqlAlchemyTestBase


class SqlAlchemyArticleAdapterTestBase(SqlAlchemyTestBase):
    """
    Base class for SqlAlchemyArticleAdapter integration tests.
    """

    def setup_method(self):
        super().setup_method()
        self.repository = SqlAlchemyArticleAdapter(self.session)

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
        content: str = "Polo",
        published_at=None,
    ) -> ArticleModel:

        model = ArticleModel()
        model.article_author_id = author_id
        model.article_title = title
        model.article_content = content
        if published_at:
            model.article_published_at = published_at

        self.session.add(model)
        self.session.commit()
        return model


class TestGetById(SqlAlchemyArticleAdapterTestBase):
    def test_get_by_id_returns_article(self):
        account = self._insert_account()
        inserted = self._insert_article(author_id=account.account_id)
        result = self.repository.get_by_id(inserted.article_id)
        assert result is not None
        assert isinstance(result, Article)
        assert result.article_title == "Test Title"

    def test_get_by_id_returns_none_if_not_found(self):
        result = self.repository.get_by_id(9999)
        assert result is None


class TestSave(SqlAlchemyArticleAdapterTestBase):
    def test_save_persists_article_to_database(self):
        account = self._insert_account()

        article = Article(
            article_id=0,
            article_author_id=account.account_id,
            article_title="Saved Article",
            article_content="New Content",
            article_published_at=None,
        )

        self.repository.save(article)
        model = self.session.query(ArticleModel).filter_by(article_title="Saved Article").first()
        assert model is not None
        assert model.article_content == "New Content"
        assert model.article_author_id == account.account_id


class TestDelete(SqlAlchemyArticleAdapterTestBase):
    def test_delete_removes_article_from_database(self):
        account = self._insert_account()
        inserted = self._insert_article(author_id=account.account_id)
        target = self.repository.get_by_id(inserted.article_id)
        assert target is not None
        self.repository.delete(target)
        check = self.repository.get_by_id(inserted.article_id)
        assert check is None


class TestPagination(SqlAlchemyArticleAdapterTestBase):
    def test_get_paginated_returns_correct_chunk(self):
        account = self._insert_account()

        for i in range(1, 4):
            self._insert_article(author_id=account.account_id, title=f"Title {i}")

        page1 = self.repository.get_paginated(page=1, per_page=2)
        assert len(page1) == 2
        page2 = self.repository.get_paginated(page=2, per_page=2)
        assert len(page2) == 1

    def test_count_all_returns_total(self):
        account = self._insert_account()
        self._insert_article(author_id=account.account_id)
        self._insert_article(author_id=account.account_id)
        total = self.repository.count_all()
        assert total == 2


class TestGetAllOrderedByDateDesc(SqlAlchemyArticleAdapterTestBase):
    def test_returns_all_articles_sorted_newest_first(self):
        from datetime import datetime, timedelta

        account = self._insert_account()
        base_time = datetime.now()
        self._insert_article(author_id=account.account_id, title="Oldest", published_at=base_time - timedelta(hours=2))
        self._insert_article(author_id=account.account_id, title="Middle", published_at=base_time - timedelta(hours=1))
        self._insert_article(author_id=account.account_id, title="Newest", published_at=base_time)
        results = self.repository.get_all_ordered_by_date_desc()
        assert len(results) == 3
        first_article = results[0]
        second_article = results[1]
        third_article = results[2]
        assert first_article.article_title == "Newest"
        assert second_article.article_title == "Middle"
        assert third_article.article_title == "Oldest"

    def test_returns_empty_list_when_no_articles(self):
        results = self.repository.get_all_ordered_by_date_desc()
        assert results == []
