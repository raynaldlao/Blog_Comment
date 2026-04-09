import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.article_request import ArticleRequest


class TestArticleRequest:
    def test_article_request_valid(self):
        req = ArticleRequest(title="A", content="B")
        assert req.title == "A"
        assert req.content == "B"

    def test_article_request_with_whitespace(self):
        req = ArticleRequest(title="  Spaced Title  ", content="   Some content.   ")
        assert req.title == "  Spaced Title  "
        assert req.content == "   Some content.   "

    def test_title_is_required(self):
        with pytest.raises(ValidationError):
            ArticleRequest(content="Some content")

    def test_content_is_required(self):
        with pytest.raises(ValidationError):
            ArticleRequest(title="Some Title")

    def test_empty_strings_are_rejected(self):
        with pytest.raises(ValidationError):
            ArticleRequest(title="", content="Valid content")

        with pytest.raises(ValidationError):
            ArticleRequest(title="Valid Title", content="")
