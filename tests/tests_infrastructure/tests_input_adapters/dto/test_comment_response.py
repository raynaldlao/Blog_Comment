from datetime import datetime

from src.application.domain.comment import Comment, CommentWithAuthor
from src.infrastructure.input_adapters.dto.comment_response import CommentResponse


def test_comment_response_from_domain_mapping():
    posted_at = datetime(2023, 10, 27, 14, 30)
    domain_comment = Comment(
        comment_id=1,
        comment_article_id=10,
        comment_written_account_id=5,
        comment_reply_to=None,
        comment_content="Hello world",
        comment_posted_at=posted_at
    )

    response = CommentResponse.from_domain(domain_comment, author_username="johndoe")
    assert response.comment_id == 1
    assert response.comment_article_id == 10
    assert response.comment_written_account_id == 5
    assert response.author_username == "johndoe"
    assert response.comment_reply_to is None
    assert response.comment_content == "Hello world"
    assert response.comment_posted_at_formatted == "October 27, 2023 at 14:30"

def test_comment_response_from_domain_with_reply():
    domain_comment = Comment(
        comment_id=2,
        comment_article_id=10,
        comment_written_account_id=6,
        comment_reply_to=1,
        comment_content="Reply content",
        comment_posted_at=datetime.now()
    )

    response = CommentResponse.from_domain(domain_comment)
    assert response.comment_reply_to == 1
    assert response.author_username == "Unknown"

def test_map_threaded_comments():
    posted_at = datetime(2023, 10, 27, 14, 30)
    comment_1 = Comment(1, 10, 1, None, "Root", posted_at)
    comment_2 = Comment(2, 10, 2, 1, "Reply", posted_at)

    threads = {
        "root": [CommentWithAuthor(comment_1, "Author1")],
        1: [CommentWithAuthor(comment_2, "Author2")]
    }

    result = CommentResponse.map_threaded_comments(threads)

    assert "root" in result
    assert 1 in result
    assert isinstance(result["root"][0], CommentResponse)
    assert result["root"][0].author_username == "Author1"
    assert result[1][0].author_username == "Author2"
    assert result[1][0].comment_reply_to == 1
