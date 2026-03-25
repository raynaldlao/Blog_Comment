from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.article import Article
from src.application.output_ports.article_repository import ArticleRepository
from src.application.services.article_management_service import ArticleManagementService


def test_create_article():
    mock_repo = MagicMock(spec=ArticleRepository)
    service = ArticleManagementService(article_repository=mock_repo)

    result = service.create_article(
        title="My First Article",
        content="Hello World!",
        author_id=1,
    )

    mock_repo.save.assert_called_once_with(result)
    assert isinstance(result, Article)
    assert result.article_title == "My First Article"
    assert result.article_content == "Hello World!"
    assert result.article_author_id == 1


def test_get_all_ordered_by_date():
    mock_repo = MagicMock(spec=ArticleRepository)
    service = ArticleManagementService(article_repository=mock_repo)

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

    mock_repo.get_all_ordered_by_date.return_value = fake_articles
    result = service.get_all_ordered_by_date()
    mock_repo.get_all_ordered_by_date.assert_called_once()
    assert len(result) == 2
    index_first_article_list = 0
    assert result[index_first_article_list].article_title == "Recent Article"


def test_get_by_id_found():
    mock_repo = MagicMock(spec=ArticleRepository)
    service = ArticleManagementService(article_repository=mock_repo)

    fake_article = Article(
        article_id=1,
        article_author_id=1,
        article_title="Found Article",
        article_content="Content",
        article_published_at=datetime.now(),
    )

    mock_repo.get_by_id.return_value = fake_article
    result = service.get_by_id(article_id=1)
    mock_repo.get_by_id.assert_called_once_with(1)
    assert result is not None
    assert result.article_title == "Found Article"


def test_get_by_id_not_found():
    mock_repo = MagicMock(spec=ArticleRepository)
    service = ArticleManagementService(article_repository=mock_repo)
    mock_repo.get_by_id.return_value = None
    result = service.get_by_id(article_id=999)
    mock_repo.get_by_id.assert_called_once_with(999)
    assert result is None
