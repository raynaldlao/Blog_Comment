from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.domain.article import Article
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.services.article_service import ArticleService


class ArticleServiceTestBase:
    def setup_method(self):
        self.mock_article_repo = MagicMock(spec=ArticleRepository)
        self.mock_account_repo = MagicMock(spec=AccountRepository)
        self.service = ArticleService(
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo
        )


class TestCreateArticle(ArticleServiceTestBase):
    def test_create_article_success(self):
        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.ADMIN,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.create_article(
            title="My First Article",
            content="Hello World !",
            author_id=fake_account.account_id,
            author_role=fake_account.account_role
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.save.assert_called_once_with(result)
        assert isinstance(result, Article)
        assert result.article_title == "My First Article"
        assert result.article_content == "Hello World !"
        assert result.article_author_id == fake_account.account_id

    def test_create_article_unauthorized_role(self):
        fake_account = Account(
            account_id=2,
            account_username="boris",
            account_password="password123",
            account_email="boris@ordinary.com",
            account_role=AccountRole.USER,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.create_article(
            title="Hacked Article",
            content="Bad Content !",
            author_id=fake_account.account_id,
            author_role=fake_account.account_role,
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.save.assert_not_called()
        assert result == "Insufficient permissions."

    def test_create_article_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        result = self.service.create_article(
            title="Ghost Article",
            content="Content from beyond!",
            author_id=999,
            author_role=AccountRole.AUTHOR,
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.save.assert_not_called()
        assert result == "Account not found."


class TestGetArticles(ArticleServiceTestBase):
    def test_get_all_ordered_by_date_desc(self):
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

        self.mock_article_repo.get_all_ordered_by_date_desc.return_value = fake_articles
        result = self.service.get_all_ordered_by_date_desc()
        self.mock_article_repo.get_all_ordered_by_date_desc.assert_called_once()
        assert len(result) == 2
        first_article_list = result[0]
        assert first_article_list.article_title == "Recent Article"

    def test_get_paginated_articles(self):
        fake_articles = [
            Article(
                article_id=1,
                article_author_id=1,
                article_title="First",
                article_content="Content 1",
                article_published_at=datetime.now(),
            ),
            Article(
                article_id=2,
                article_author_id=1,
                article_title="Second",
                article_content="Content 2",
                article_published_at=datetime.now(),
            )
        ]

        self.mock_article_repo.get_paginated.return_value = fake_articles
        result = self.service.get_paginated_articles(page=2, per_page=10)
        self.mock_article_repo.get_paginated.assert_called_once_with(2, 10)
        assert len(result) == 2
        first_article_list = result[0]
        second_article_list = result[1]
        assert first_article_list.article_title == "First"
        assert second_article_list.article_title == "Second"

    def test_get_paginated_articles_page_less_than_one(self):
        fake_articles = [
            Article(
                article_id=1,
                article_author_id=1,
                article_title="Paged Title",
                article_content="Paged Content",
                article_published_at=datetime.now(),
            )
        ]

        self.mock_article_repo.get_paginated.return_value = fake_articles
        result = self.service.get_paginated_articles(page=-5, per_page=10)
        self.mock_article_repo.get_paginated.assert_called_once_with(1, 10)
        assert len(result) == 1

    def test_get_paginated_articles_defaults(self):
        self.mock_article_repo.get_paginated.return_value = []
        self.service.get_paginated_articles()
        page = 1
        per_page = 10
        self.mock_article_repo.get_paginated.assert_called_once_with(page, per_page)

    def test_get_total_count(self):
        self.mock_article_repo.count_all.return_value = 42
        result = self.service.get_total_count()
        self.mock_article_repo.count_all.assert_called_once()
        assert result == 42


class TestGetArticleById(ArticleServiceTestBase):
    def test_get_by_id_found(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="Found Article",
            article_content="Content",
            article_published_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article
        result = self.service.get_by_id(article_id=fake_article.article_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        assert result is not None
        assert result.article_title == "Found Article"

    def test_get_by_id_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None
        result = self.service.get_by_id(article_id=999)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        assert result is None


class TestUpdateArticle(ArticleServiceTestBase):
    def test_update_article_success(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="Old Title",
            article_content="Old Content",
            article_published_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article

        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            title="New Title",
            content="New Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        assert result is not None
        assert result.article_title == "New Title"
        assert result.article_content == "New Content"

    def test_update_article_unauthorized(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="Old Title",
            article_content="Old Content",
            article_published_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article

        fake_account = Account(
            account_id=99,
            account_username="hacker",
            account_password="password123",
            account_email="hacker@cyber.com",
            account_role=AccountRole.ADMIN,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            title="Hacked Title",
            content="Hacked Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        assert result == "Unauthorized : You are not the author of this article."

    def test_update_article_insufficient_role(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="Old Title",
            article_content="Old Content",
            article_published_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article

        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.USER,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            title="Hacked Title",
            content="Hacked Content",
        )

        self.mock_article_repo.get_by_id.assert_not_called()
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        assert result == "Insufficient permissions."

    def test_update_article_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None

        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=datetime.now(),
        )

        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=999,
            user_id=fake_account.account_id,
            title="New Title",
            content="New Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        assert result == "Article not found."


class TestDeleteArticle(ArticleServiceTestBase):
    def test_delete_article_success_by_author(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="To Be Deleted",
            article_content="Delete me",
            article_published_at=datetime.now(),
        )

        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_called_once_with(fake_article)
        assert result is True

    def test_delete_article_success_by_admin(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="To Be Deleted",
            article_content="Delete me",
            article_published_at=datetime.now(),
        )

        fake_admin = Account(
            account_id=99,
            account_username="admin2",
            account_password="password123",
            account_email="admin@cyber.com",
            account_role=AccountRole.ADMIN,
            account_created_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_admin
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_admin.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_admin.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_called_once_with(fake_article)
        assert result is True

    def test_delete_article_unauthorized_ownership(self):
        fake_article = Article(
            article_id=1,
            article_author_id=1,
            article_title="To Be Deleted",
            article_content="Delete me",
            article_published_at=datetime.now(),
        )

        fake_author_other = Account(
            account_id=99,
            account_username="other",
            account_password="password123",
            account_email="other@cyber.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_author_other
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_author_other.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_author_other.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_not_called()
        assert result == "Unauthorized : Only authors or admins can delete articles."

    def test_delete_article_not_found(self):
        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=datetime.now(),
        )

        self.mock_article_repo.get_by_id.return_value = None
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.delete_article(article_id=999, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.delete.assert_not_called()
        assert result == "Article not found."
