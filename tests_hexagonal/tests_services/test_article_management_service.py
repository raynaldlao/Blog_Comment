from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account
from src.application.domain.article import Article
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.services.article_management_service import ArticleManagementService


def test_create_article_success():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="admin",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account

    result = service.create_article(
        title="My First Article",
        content="Hello World !",
        author_id=fake_account.account_id,
        author_role=fake_account.account_role
    )

    mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
    mock_article_repo.save.assert_called_once_with(result)
    assert isinstance(result, Article)
    assert result.article_title == "My First Article"
    assert result.article_content == "Hello World !"
    assert result.article_author_id == fake_account.account_id


def test_create_article_unauthorized_role():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_account = Account(
        account_id=2,
        account_username="boris",
        account_password="password123",
        account_email="boris@ordinary.com",
        account_role="user",
        account_created_at=datetime.now(),
    )

    mock_account_repo.get_by_id.return_value = fake_account

    result = service.create_article(
        title="Hacked Article",
        content="Bad Content !",
        author_id=fake_account.account_id,
        author_role=fake_account.account_role,
    )

    mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
    mock_article_repo.save.assert_not_called()
    assert result is None


def test_create_article_account_not_found():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    mock_account_repo.get_by_id.return_value = None

    result = service.create_article(
        title="Ghost Article",
        content="Content from beyond!",
        author_id=999,
        author_role="author",
    )

    mock_account_repo.get_by_id.assert_called_once_with(999)
    mock_article_repo.save.assert_not_called()
    assert result is None


def test_get_all_ordered_by_date_desc():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_articles = [
        Article(
            article_id=2,
            article_author_id=1,
            article_title="Recent Article",
            article_content="Content 2",
            article_published_at=datetime(2026, 3, 25),
        ),
        Article(
            article_id=1,
            article_author_id=1,
            article_title="Old Article",
            article_content="Content 1",
            article_published_at=datetime(2026, 1, 1),
        ),
    ]

    mock_article_repo.get_all_ordered_by_date_desc.return_value = fake_articles
    result = service.get_all_ordered_by_date_desc()
    mock_article_repo.get_all_ordered_by_date_desc.assert_called_once()
    assert len(result) == 2
    index_first_article_list = 0
    assert result[index_first_article_list].article_title == "Recent Article"


def test_get_by_id_found():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=1,
        article_title="Found Article",
        article_content="Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article
    result = service.get_by_id(article_id=1)
    mock_article_repo.get_by_id.assert_called_once_with(1)
    assert result is not None
    assert result.article_title == "Found Article"


def test_get_by_id_not_found():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    mock_article_repo.get_by_id.return_value = None
    result = service.get_by_id(article_id=999)
    mock_article_repo.get_by_id.assert_called_once_with(999)
    assert result is None


def test_update_article_success():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=1,
        article_title="Old Title",
        article_content="Old Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="author",
        account_created_at=datetime.now(),
    )
    mock_account_repo.get_by_id.return_value = fake_account

    result = service.update_article(
        article_id=1,
        user_id=fake_account.account_id,
        title="New Title",
        content="New Content",
    )

    mock_article_repo.get_by_id.assert_called_once_with(1)
    mock_account_repo.get_by_id.assert_called_once_with(1)
    assert result is not None
    assert result.article_title == "New Title"
    assert result.article_content == "New Content"


def test_update_article_unauthorized():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=1,
        article_title="Old Title",
        article_content="Old Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article

    fake_account = Account(
        account_id=99,
        account_username="hacker",
        account_password="password123",
        account_email="hacker@cyber.com",
        account_role="admin",
        account_created_at=datetime.now(),
    )
    mock_account_repo.get_by_id.return_value = fake_account

    result = service.update_article(
        article_id=1,
        user_id=fake_account.account_id,
        title="Hacked Title",
        content="Hacked Content",
    )

    mock_article_repo.get_by_id.assert_called_once_with(1)
    assert result is None


def test_update_article_insufficient_role():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    fake_article = Article(
        article_id=1,
        article_author_id=1,
        article_title="Old Title",
        article_content="Old Content",
        article_published_at=datetime.now(),
    )

    mock_article_repo.get_by_id.return_value = fake_article

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=datetime.now(),
    )
    mock_account_repo.get_by_id.return_value = fake_account

    result = service.update_article(
        article_id=1,
        user_id=1,
        title="Hacked Title",
        content="Hacked Content",
    )

    mock_article_repo.get_by_id.assert_called_once_with(1)
    mock_account_repo.get_by_id.assert_called_once_with(1)
    assert result is None


def test_update_article_not_found():
    mock_article_repo = MagicMock(spec=ArticleRepository)
    mock_account_repo = MagicMock(spec=AccountRepository)

    service = ArticleManagementService(
        article_repository=mock_article_repo,
        account_repository=mock_account_repo
    )

    mock_article_repo.get_by_id.return_value = None

    result = service.update_article(
        article_id=999,
        user_id=1,
        title="New Title",
        content="New Content",
    )

    mock_article_repo.get_by_id.assert_called_once_with(999)
    assert result is None
