from datetime import datetime

from src.application.domain.article import Article
from src.infrastructure.input_adapters.dto.article_response import ArticleResponse


class TestArticleResponse:
    def test_from_domain_conversion(self):
        domain_article = Article(
            article_id=1,
            article_author_id=10,
            article_title="Test Title",
            article_content="Test Content with enough length for meta description generation purposes.",
            article_published_at=datetime(2023, 10, 27)
        )

        response = ArticleResponse.from_domain(domain_article, author_username="JohnDoe")
        assert response.article_id == 1
        assert response.article_title == "Test Title"
        assert response.author_username == "JohnDoe"
        assert response.article_published_at_formatted == "October 27, 2023"
        assert "Test Content" in response.meta_description

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
        assert response.article_published_at_formatted == ""
