import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.article_request import ArticleRequest


class TestArticleRequest:
    def test_valid_article_request(self):
        req = ArticleRequest(title="Valid Title", content="This is a valid long enough content.")
        assert req.title == "Valid Title"
        assert req.content == "This is a valid long enough content."

    def test_article_request_strips_whitespace(self):
        req = ArticleRequest(title="  Spaced Title  ", content="   Some spaced content.   ")
        assert req.title == "Spaced Title"
        assert req.content == "Some spaced content."

    def test_missing_title(self):
        with pytest.raises(ValidationError) as exc_info:
            ArticleRequest(content="Valid content here.")
        assert "Field required" in str(exc_info.value)

    def test_title_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            ArticleRequest(title="A", content="Valid content here.")
        assert "String should have at least 3 characters" in str(exc_info.value)

    def test_content_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            ArticleRequest(title="Valid Title", content="Too short")
        assert "String should have at least 10 characters" in str(exc_info.value)
