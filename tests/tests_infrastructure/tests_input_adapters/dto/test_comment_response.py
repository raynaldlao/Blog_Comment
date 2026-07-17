from datetime import datetime

from src.application.domain.comment import Comment, CommentNode, CommentWithAuthor
from src.infrastructure.input_adapters.dto.comment_response import CommentNodeResponse, CommentResponse


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

def test_comment_response_from_domain_legacy_deleted_maps_to_anonymous():
    domain_comment = Comment(
        comment_id=3,
        comment_article_id=10,
        comment_written_account_id=5,
        comment_reply_to=None,
        comment_content="[deleted]",
        comment_posted_at=datetime.now()
    )

    response = CommentResponse.from_domain(domain_comment, author_username="original_user")
    assert response.author_username == "Anonymous"
    assert response.comment_content == "[deleted]"

def test_map_nested_tree():
    posted_at = datetime(2023, 10, 27, 14, 30)
    comment_1 = Comment(1, 10, 1, None, "Root", posted_at)
    comment_2 = Comment(2, 10, 2, 1, "Reply", posted_at)

    nodes = [
        CommentNode(
            comment=CommentWithAuthor(comment_1, "Author1"),
            replies=[
                CommentNode(
                    comment=CommentWithAuthor(comment_2, "Author2"),
                    depth=1
                )
            ],
            depth=0
        )
    ]

    result = CommentResponse.map_nested_tree(nodes)

    assert len(result) == 1
    assert isinstance(result[0], CommentNodeResponse)
    assert result[0].comment.author_username == "Author1"
    assert result[0].depth == 0
    assert len(result[0].replies) == 1
    assert result[0].replies[0].comment.author_username == "Author2"
    assert result[0].replies[0].comment.comment_reply_to == 1
    assert result[0].replies[0].depth == 1

def test_from_domain_with_avatar_file_id():
    comment = Comment(1, 10, 5, None, "Hello", datetime(2023, 10, 27, 14, 30))
    result = CommentResponse.from_domain(comment, "yoda", "abc-123")
    assert result.author_avatar_file_id == "abc-123"

def test_from_domain_without_avatar_file_id():
    comment = Comment(1, 10, 5, None, "Hello", datetime(2023, 10, 27, 14, 30))
    result = CommentResponse.from_domain(comment, "yoda")
    assert result.author_avatar_file_id is None

def test_from_domain_with_none_author_id_maps_to_removed():
    comment = Comment(
        comment_id=4,
        comment_article_id=10,
        comment_written_account_id=None,
        comment_reply_to=None,
        comment_content="Original content",
        comment_posted_at=datetime.now()
    )
    result = CommentResponse.from_domain(comment, "some_user")
    assert result.author_username == "Anonymous"
    assert result.comment_written_account_id is None
    assert result.comment_content == "<em>Comment removed</em>"

def test_map_nested_tree_threads_avatar():
    posted_at = datetime(2023, 10, 27, 14, 30)
    comment_1 = Comment(1, 10, 1, None, "Root", posted_at)
    comment_2 = Comment(2, 10, 2, 1, "Reply", posted_at)
    nodes = [
        CommentNode(
            comment=CommentWithAuthor(comment_1, "Author1", "avatar-1"),
            replies=[
                CommentNode(
                    comment=CommentWithAuthor(comment_2, "Author2", "avatar-2"),
                    depth=1,
                )
            ],
            depth=0,
        )
    ]
    result = CommentResponse.map_nested_tree(nodes)
    assert result[0].comment.author_avatar_file_id == "avatar-1"
    assert result[0].replies[0].comment.author_avatar_file_id == "avatar-2"

def test_map_nested_tree_shallow_no_flatten():
    posted_at = datetime(2023, 10, 27, 14, 30)
    c1 = Comment(1, 10, 1, None, "Root", posted_at)
    c2 = Comment(2, 10, 2, 1, "Lvl1", posted_at)
    c3 = Comment(3, 10, 3, 2, "Lvl2", posted_at)
    nodes = [
        CommentNode(
            comment=CommentWithAuthor(c1, "U1"),
            replies=[
                CommentNode(
                    comment=CommentWithAuthor(c2, "U2"),
                    replies=[
                        CommentNode(
                            comment=CommentWithAuthor(c3, "U3"),
                            depth=2,
                        )
                    ],
                    depth=1,
                )
            ],
            depth=0,
        )
    ]
    result = CommentResponse.map_nested_tree(nodes)
    assert len(result) == 1
    assert result[0].depth == 0
    assert len(result[0].replies) == 1
    assert result[0].replies[0].depth == 1
    assert len(result[0].replies[0].replies) == 1
    assert result[0].replies[0].replies[0].depth == 2

def test_map_nested_tree_truncate_deep():
    posted_at = datetime(2023, 10, 27, 14, 30)
    c1 = Comment(1, 10, 1, None, "Root", posted_at)
    c2 = Comment(2, 10, 2, 1, "Lvl1", posted_at)
    c3 = Comment(3, 10, 3, 2, "Lvl2", posted_at)
    c4 = Comment(4, 10, 4, 3, "Lvl3", posted_at)
    c5 = Comment(5, 10, 5, 4, "Lvl4", posted_at)
    nodes = [
        CommentNode(
            comment=CommentWithAuthor(c1, "U1"),
            replies=[
                CommentNode(
                    comment=CommentWithAuthor(c2, "U2"),
                    replies=[
                        CommentNode(
                            comment=CommentWithAuthor(c3, "U3"),
                            replies=[
                                CommentNode(
                                    comment=CommentWithAuthor(c4, "U4"),
                                    replies=[
                                        CommentNode(
                                            comment=CommentWithAuthor(c5, "U5"),
                                            depth=4,
                                        )
                                    ],
                                    depth=3,
                                )
                            ],
                            depth=2,
                        )
                    ],
                    depth=1,
                )
            ],
            depth=0,
        )
    ]
    result = CommentResponse.map_nested_tree(nodes)
    assert len(result) == 1
    root = result[0]
    assert root.depth == 0
    assert len(root.replies) == 1
    lvl1 = root.replies[0]
    assert lvl1.depth == 1
    assert len(lvl1.replies) == 1
    lvl2 = lvl1.replies[0]
    assert lvl2.depth == 2
    assert len(lvl2.replies) == 1
    lvl3 = lvl2.replies[0]
    assert lvl3.comment.comment_id == 4
    assert lvl3.depth == 3
    assert len(lvl3.replies) == 0
    assert lvl3.comment.comment_content == "Lvl3"

def test_map_nested_tree_flatten_multiple_children():
    posted_at = datetime(2023, 10, 27, 14, 30)
    c1 = Comment(1, 10, 1, None, "Root", posted_at)
    c2 = Comment(2, 10, 2, 1, "Lvl1_A", posted_at)
    c3 = Comment(3, 10, 3, 1, "Lvl1_B", posted_at)
    c4 = Comment(4, 10, 4, 2, "Lvl2", posted_at)
    nodes = [
        CommentNode(
            comment=CommentWithAuthor(c1, "U1"),
            replies=[
                CommentNode(
                    comment=CommentWithAuthor(c2, "U2"),
                    replies=[
                        CommentNode(
                            comment=CommentWithAuthor(c4, "U4"),
                            depth=2,
                        )
                    ],
                    depth=1,
                ),
                CommentNode(
                    comment=CommentWithAuthor(c3, "U3"),
                    depth=1,
                ),
            ],
            depth=0,
        )
    ]
    result = CommentResponse.map_nested_tree(nodes)
    assert len(result) == 1
    assert len(result[0].replies) == 2
    assert result[0].replies[0].comment.comment_id == 2
    assert result[0].replies[0].depth == 1
    assert result[0].replies[1].comment.comment_id == 3
    assert result[0].replies[1].depth == 1
