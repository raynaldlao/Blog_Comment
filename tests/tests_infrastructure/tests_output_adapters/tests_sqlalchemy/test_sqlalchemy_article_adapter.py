import pytest

from src.application.domain.article import Article
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from tests.test_domain_factories import create_test_article
from tests.tests_infrastructure.tests_output_adapters.tests_sqlalchemy.sqlalchemy_test_utils import (
    AccountDataBuilder,
    ArticleDataBuilder,
    SqlAlchemyTestBase,
)


class SqlAlchemyArticleAdapterTestBase(SqlAlchemyTestBase):
    @pytest.fixture(autouse=True)
    def setup_adapter(self):
        self.repository = SqlAlchemyArticleAdapter(self.session)
        self.article_builder = ArticleDataBuilder(self.session)
        self.account_builder = AccountDataBuilder(self.session)


class TestArticleGetById(SqlAlchemyArticleAdapterTestBase):
    def test_get_by_id_returns_article(self):
        account = self.account_builder.create()
        inserted = self.article_builder.create(author_id=account.account_id)
        result = self.repository.get_by_id(inserted.article_id)
        assert result is not None
        assert isinstance(result, Article)
        assert result.article_title == "Test Title"

    def test_get_by_id_returns_none_if_not_found(self):
        result = self.repository.get_by_id(9999)
        assert result is None


class TestArticleSave(SqlAlchemyArticleAdapterTestBase):
    def test_save_persists_article_to_database(self):
        account = self.account_builder.create()

        article = create_test_article(
            article_id=0,
            article_author_id=account.account_id,
            article_title="Saved Article",
            article_content="New Content",
        )

        self.repository.save(article)
        assert article.article_id > 0
        model = self.session.query(ArticleModel).filter_by(article_title="Saved Article").first()
        assert model is not None
        assert model.article_content == "New Content"
        assert model.article_author_id == account.account_id

    def test_save_updates_existing_article(self):
        account = self.account_builder.create()
        inserted = self.article_builder.create(
            author_id=account.account_id,
            title="Original Title",
            content="Original Content",
        )

        updated_article = create_test_article(
            article_id=inserted.article_id,
            article_author_id=account.account_id,
            article_title="Updated Title",
            article_content="Updated Content",
        )

        self.repository.save(updated_article)
        result = self.repository.get_by_id(inserted.article_id)
        assert result is not None
        assert result.article_title == "Updated Title"
        assert result.article_content == "Updated Content"


class TestArticleDelete(SqlAlchemyArticleAdapterTestBase):
    def test_delete_removes_article_from_database(self):
        account = self.account_builder.create()
        inserted = self.article_builder.create(author_id=account.account_id)
        target = self.repository.get_by_id(inserted.article_id)
        assert target is not None
        self.repository.delete(target)
        check = self.repository.get_by_id(inserted.article_id)
        assert check is None


class TestArticlePagination(SqlAlchemyArticleAdapterTestBase):
    def test_get_paginated_returns_correct_chunk(self):
        account = self.account_builder.create()

        for i in range(1, 4):
            self.article_builder.create(author_id=account.account_id, title=f"Title {i}")

        page1 = self.repository.get_paginated(page=1, per_page=2)
        assert len(page1) == 2
        page2 = self.repository.get_paginated(page=2, per_page=2)
        assert len(page2) == 1

    def test_count_all_returns_total(self):
        account = self.account_builder.create()
        self.article_builder.create(author_id=account.account_id)
        self.article_builder.create(author_id=account.account_id)
        total = self.repository.count_all()
        assert total == 2


class TestArticleGetAllOrderedByDateDesc(SqlAlchemyArticleAdapterTestBase):
    def test_returns_all_articles_sorted_newest_first(self):
        from datetime import datetime, timedelta

        account = self.account_builder.create()
        base_time = datetime.now()
        self.article_builder.create(author_id=account.account_id, title="Oldest", published_at=base_time - timedelta(hours=2))
        self.article_builder.create(author_id=account.account_id, title="Middle", published_at=base_time - timedelta(hours=1))
        self.article_builder.create(author_id=account.account_id, title="Newest", published_at=base_time)
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


class TestArticleSearch(SqlAlchemyArticleAdapterTestBase):
    def test_search_by_author_name(self):
        author = self.account_builder.create(username="john_doe", email="john@test.com")
        self.article_builder.create(author_id=author.account_id, title="Post One")
        self.article_builder.create(author_id=author.account_id, title="Post Two")
        other = self.account_builder.create(username="jane_doe", email="jane@test.com")
        self.article_builder.create(author_id=other.account_id, title="Jane Post")
        results = self.repository.search("john", page=1, per_page=10)
        assert len(results) == 2
        assert all("Post" in a.article_title for a in results)

    def test_search_by_author_case_insensitive(self):
        author = self.account_builder.create(username="JohnDoe", email="johncase@test.com")
        self.article_builder.create(author_id=author.account_id, title="Some Post")
        results = self.repository.search("johndoe", page=1, per_page=10)
        assert len(results) == 1

    def test_search_by_author_no_match(self):
        author = self.account_builder.create(username="alice", email="alice@test.com")
        self.article_builder.create(author_id=author.account_id, title="Post")
        results = self.repository.search("inexistant", page=1, per_page=10)
        assert results == []

    def test_search_title_still_works_with_join(self):
        author = self.account_builder.create(username="someauthor", email="some@test.com")
        self.article_builder.create(author_id=author.account_id, title="Unique Title")
        self.article_builder.create(author_id=author.account_id, title="Other")
        results = self.repository.search("Unique", page=1, per_page=10)
        assert len(results) == 1
        assert results[0].article_title == "Unique Title"

    def test_count_search_by_author(self):
        author = self.account_builder.create(username="bob", email="bob@test.com")
        self.article_builder.create(author_id=author.account_id, title="Post 1")
        self.article_builder.create(author_id=author.account_id, title="Post 2")
        assert self.repository.count_search("bob") == 2
        assert self.repository.count_search("alice") == 0
