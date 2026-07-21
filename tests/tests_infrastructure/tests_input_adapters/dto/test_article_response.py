from datetime import UTC, datetime

from src.application.domain.article import Article
from src.infrastructure.input_adapters.dto.article_response import ArticleResponse


class TestArticleResponse:
    def test_from_domain_conversion(self):
        dt = datetime(2023, 10, 27)
        domain_article = Article(
            article_id=1,
            article_author_id=10,
            article_title="Test Title",
            article_description="A short description",
            article_content="Test Content with enough length for meta description generation purposes.",
            article_published_at=dt
        )

        response = ArticleResponse.from_domain(domain_article, author_username="JohnDoe")
        assert response.article_id == 1
        assert response.article_title == "Test Title"
        assert response.author_username == "JohnDoe"
        assert response.article_published_at == dt
        assert response.article_description == "A short description"
        assert response.meta_description == "A short description"

    def test_from_domain_with_null_date(self):
        domain_article = Article(
            article_id=1,
            article_author_id=10,
            article_title="Test Title",
            article_content="Test Content",
            article_published_at=None
        )

        response = ArticleResponse.from_domain(domain_article, author_username="Guest")
        assert response.author_username == "Guest"
        assert response.article_published_at is None

    def test_from_domain_with_avatar_file_id(self):
        domain_article = Article(
            article_id=1, article_author_id=10, article_title="Title",
            article_content="Content", article_published_at=datetime.now()
        )
        result = ArticleResponse.from_domain(domain_article, "yoda", "abc-123")
        assert result.author_avatar_file_id == "abc-123"

    def test_from_domain_without_avatar_file_id(self):
        domain_article = Article(
            article_id=1, article_author_id=10, article_title="Title",
            article_content="Content", article_published_at=datetime.now()
        )
        result = ArticleResponse.from_domain(domain_article, "yoda")
        assert result.author_avatar_file_id is None

    def test_from_domain_with_none_author_id(self):
        domain_article = Article(
            article_id=1, article_author_id=None, article_title="Title",
            article_content="Content", article_published_at=datetime.now()
        )
        result = ArticleResponse.from_domain(domain_article, "Anonymous")
        assert result.article_author_id is None
        assert result.author_username == "Anonymous"

    def test_from_domain_with_description(self):
        dt = datetime(2023, 10, 27)
        domain_article = Article(
            article_id=1, article_author_id=10, article_title="Title",
            article_description="My short description",
            article_content="Content", article_published_at=dt
        )
        result = ArticleResponse.from_domain(domain_article, "yoda")
        assert result.article_description == "My short description"
        assert result.meta_description == "My short description"

    def test_from_domain_with_article_edited_at(self):
        """article_edited_at formaté en Europe/Paris (UTC+1 en janvier)."""
        dt = datetime(2023, 1, 27, 12, 0, 0, tzinfo=UTC)
        domain_article = Article(
            article_id=1, article_author_id=10, article_title="Title",
            article_content="Content", article_published_at=datetime.now(),
            article_edited_at=dt,
        )
        response = ArticleResponse.from_domain(domain_article, "user")
        assert response.article_edited_at == dt
        assert response.article_edited_at_formatted == "January 27, 2023 at 13:00"

    def test_from_domain_without_article_edited_at(self):
        """article_edited_at_formatted vide si jamais édité."""
        domain_article = Article(
            article_id=1, article_author_id=10, article_title="Title",
            article_content="Content", article_published_at=datetime.now(),
        )
        response = ArticleResponse.from_domain(domain_article, "user")
        assert response.article_edited_at is None
        assert response.article_edited_at_formatted == ""
