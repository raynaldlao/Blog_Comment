
import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.comment_request import CommentRequest


def test_comment_request_valid_data():
    req = CommentRequest(content="This is a valid comment.")
    assert req.content == "This is a valid comment."

def test_comment_request_empty_content_fails():
    with pytest.raises(ValidationError):
        CommentRequest(content="")

def test_comment_request_missing_content_fails():
    with pytest.raises(ValidationError):
        CommentRequest.model_validate({})

def test_comment_request_content_too_long_fails():
    with pytest.raises(ValidationError):
        CommentRequest(content="x" * 5001)

def test_comment_request_html_only_content_fails():
    with pytest.raises(ValidationError):
        CommentRequest(content="<p><br></p>")

def test_comment_request_html_spaces_only_fails():
    with pytest.raises(ValidationError):
        CommentRequest(content="<p> </p>")

def test_comment_request_html_with_text_passes():
    req = CommentRequest(content="<p>Hello</p>")
    assert req.content == "<p>Hello</p>"
