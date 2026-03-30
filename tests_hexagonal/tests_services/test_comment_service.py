from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account
from src.application.domain.article import Article
from src.application.domain.comment import Comment
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.comment_service import CommentService


def test_create_comment_success():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account

    fake_article = Article(
        article_id=1,
        article_author_id=2,
        article_title="My Article",
        article_content="Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article

    result = service.create_comment(
        article_id=fake_article.article_id,
        user_id=fake_account.account_id,
        content="Great post!"
    )

    mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
    mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
    mock_comment_repo.save.assert_called_once()
    index_args = 0
    index_kwargs = 0
    saved_comment = mock_comment_repo.save.call_args[index_args][index_kwargs]
    assert saved_comment.comment_article_id == fake_article.article_id
    assert saved_comment.comment_written_account_id == fake_account.account_id
    assert saved_comment.comment_reply_to is None
    assert saved_comment.comment_content == "Great post!"
    assert result is saved_comment


def test_create_comment_account_not_found():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    mock_account_repo.get_by_id.return_value = None

    result = service.create_comment(
        article_id=1,
        user_id=999,
        content="This will not post."
    )

    mock_account_repo.get_by_id.assert_called_once_with(999)
    mock_article_repo.get_by_id.assert_not_called()
    mock_comment_repo.save.assert_not_called()
    assert result == "Account not found."


def test_create_comment_article_not_found():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account
    mock_article_repo.get_by_id.return_value = None

    result = service.create_comment(
        article_id=999,
        user_id=fake_account.account_id,
        content="Writing in the void."
    )

    mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
    mock_article_repo.get_by_id.assert_called_once_with(999)
    mock_comment_repo.save.assert_not_called()
    assert result == "Article not found."


def test_create_reply_success_root_comment():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account

    parent_comment = Comment(
        comment_id=10,
        comment_article_id=5,
        comment_written_account_id=2,
        comment_reply_to=None,
        comment_content="Root comment",
        comment_posted_at=datetime.now(),
    )

    mock_comment_repo.get_by_id.return_value = parent_comment
    result = service.create_reply(parent_comment_id=parent_comment.comment_id, user_id=fake_account.account_id, content="This is a reply")
    mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
    mock_comment_repo.get_by_id.assert_called_once_with(parent_comment.comment_id)
    mock_comment_repo.save.assert_called_once()
    index_args = 0
    index_kwargs = 0
    saved_reply = mock_comment_repo.save.call_args[index_args][index_kwargs]

    assert saved_reply.comment_article_id == parent_comment.comment_article_id
    assert saved_reply.comment_written_account_id == fake_account.account_id
    assert saved_reply.comment_reply_to == parent_comment.comment_id
    assert saved_reply.comment_content == "This is a reply"
    assert result is saved_reply


def test_create_reply_success_nested_comment():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account

    parent_comment = Comment(
        comment_id=15,
        comment_article_id=5,
        comment_written_account_id=2,
        comment_reply_to=10,
        comment_content="I am a reply",
        comment_posted_at=datetime.now(),
    )
    mock_comment_repo.get_by_id.return_value = parent_comment
    result = service.create_reply(parent_comment_id=parent_comment.comment_id, user_id=fake_account.account_id, content="Replying to a reply")
    mock_comment_repo.save.assert_called_once()
    index_args = 0
    index_kwargs = 0
    saved_reply = mock_comment_repo.save.call_args[index_args][index_kwargs]
    assert saved_reply.comment_reply_to == 10
    assert result is saved_reply


def test_create_reply_parent_not_found():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account
    mock_comment_repo.get_by_id.return_value = None
    result = service.create_reply(parent_comment_id=999, user_id=fake_account.account_id, content="Replying to nothing")
    mock_comment_repo.get_by_id.assert_called_once_with(999)
    mock_comment_repo.save.assert_not_called()
    assert result == "Parent comment not found."


def test_get_comments_for_article_not_found():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    mock_article_repo.get_by_id.return_value = None
    result = service.get_comments_for_article(article_id=999)
    mock_article_repo.get_by_id.assert_called_once_with(999)
    mock_comment_repo.get_all_by_article_id.assert_not_called()
    assert result == "Article not found."


def test_get_comments_for_article_empty():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=2,
        article_title="My Article",
        article_content="Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article
    mock_comment_repo.get_all_by_article_id.return_value = []
    result = service.get_comments_for_article(article_id=fake_article.article_id)
    mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
    mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
    assert isinstance(result, dict)
    assert result == {"root": []}


def test_get_comments_for_article_success():
    mock_comment_repo = MagicMock(spec=CommentRepository)
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = CommentService(
        comment_repository=mock_comment_repo,
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=2,
        article_title="My Article",
        article_content="Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article

    root_comment = Comment(
        comment_id=10,
        comment_article_id=fake_article.article_id,
        comment_written_account_id=3,
        comment_reply_to=None,
        comment_content="First!",
        comment_posted_at=datetime.now(),
    )

    reply = Comment(
        comment_id=15,
        comment_article_id=fake_article.article_id,
        comment_written_account_id=4,
        comment_reply_to=root_comment.comment_id,
        comment_content="Awesome!",
        comment_posted_at=datetime.now(),
    )

    mock_comment_repo.get_all_by_article_id.return_value = [root_comment, reply]
    result = service.get_comments_for_article(article_id=fake_article.article_id)
    mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
    mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
    assert isinstance(result, dict)
    assert "root" in result
    assert result["root"] == [root_comment]
    comment_id_key = root_comment.comment_id
    assert comment_id_key in result
    assert result[comment_id_key] == [reply]
