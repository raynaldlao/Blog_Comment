
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
