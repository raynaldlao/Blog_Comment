from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import AccountRole
from src.application.domain.article import Article
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.article_service import ArticleService
from tests_hexagonal.test_domain_factories import (
    create_test_account,
    create_test_article,
    create_test_comment,
)


class ArticleServiceTestBase:
    def setup_method(self):
        self.mock_article_repo = MagicMock(spec=ArticleRepository, autospec=True)
        self.mock_account_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.mock_comment_repo = MagicMock(spec=CommentRepository, autospec=True)
        self.service = ArticleService(
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo,
            comment_repository=self.mock_comment_repo
        )


class TestCreateArticle(ArticleServiceTestBase):
    def test_create_article_success(self):
        fake_account = create_test_account(account_role=AccountRole.ADMIN)

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
        fake_account = create_test_account(
            account_id=2,
            account_username="boris",
            account_email="boris@ordinary.com",
            account_role=AccountRole.USER
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
            create_test_article(
                article_id=2,
                article_title="Recent Article",
                article_published_at=datetime(2026, 3, 25),
            ),
            create_test_article(
                article_id=1,
                article_title="Old Article",
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
            create_test_article(article_id=1, article_title="First", article_author_id=10),
            create_test_article(article_id=2, article_title="Second", article_author_id=20)
        ]

        fake_authors = [
            create_test_account(account_id=10, account_username="Author1"),
            create_test_account(account_id=20, account_username="Author2")
        ]

        self.mock_article_repo.get_paginated.return_value = fake_articles
        self.mock_account_repo.get_by_ids.return_value = fake_authors
        articles = self.service.get_paginated_articles(page=2, per_page=10)
        article_1, article_2 = articles
        assert article_1.article.article_title == "First"
        assert article_1.author_name == "Author1"
        assert article_2.article.article_title == "Second"
        assert article_2.author_name == "Author2"

    def test_get_paginated_articles_page_less_than_one(self):
        fake_articles = [create_test_article(article_title="Paged Title", article_author_id=1)]
        self.mock_article_repo.get_paginated.return_value = fake_articles
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1, account_username="User")]
        articles = self.service.get_paginated_articles(page=-5, per_page=10)
        article_view, = articles
        assert article_view.author_name == "User"

    def test_get_paginated_articles_defaults(self):
        self.mock_article_repo.get_paginated.return_value = []
        self.mock_account_repo.get_by_ids.return_value = []
        self.service.get_paginated_articles()
        self.mock_article_repo.get_paginated.assert_called_once_with(1, 10)

    def test_get_total_count(self):
        self.mock_article_repo.count_all.return_value = 42
        result = self.service.get_total_count()
        self.mock_article_repo.count_all.assert_called_once()
        assert result == 42

    def test_get_paginated_articles_deduplication(self):
        same_author_id = 99
        fake_articles = [
            create_test_article(article_id=1, article_author_id=same_author_id),
            create_test_article(article_id=2, article_author_id=same_author_id),
            create_test_article(article_id=3, article_author_id=42)
        ]

        self.mock_article_repo.get_paginated.return_value = fake_articles
        self.mock_account_repo.get_by_ids.return_value = [
            create_test_account(account_id=99, account_username="Author99"),
            create_test_account(account_id=42, account_username="Author42")
        ]

        self.service.get_paginated_articles()
        called_ids = self.mock_account_repo.get_by_ids.call_args[0][0]
        assert len(called_ids) == 2
        assert set(called_ids) == {99, 42}
        self.mock_account_repo.get_by_id.assert_not_called()

    def test_get_paginated_articles_unknown_author(self):
        fake_articles = [create_test_article(article_id=1, article_author_id=999)]
        self.mock_article_repo.get_paginated.return_value = fake_articles
        self.mock_account_repo.get_by_ids.return_value = []
        result = self.service.get_paginated_articles()
        assert result[0].author_name == "Unknown"


class TestGetArticleById(ArticleServiceTestBase):
    def test_get_by_id_found(self):
        fake_article = create_test_article(article_title="Found Article")
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
        fake_article = create_test_article(article_id=1, article_title="Old Title")
        self.mock_article_repo.get_by_id.return_value = fake_article
        fake_account = create_test_account(account_id=1, account_role=AccountRole.AUTHOR)
        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            title="New Title",
            content="New Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.save.assert_called_once_with(result)
        assert isinstance(result, Article)
        assert result.article_title == "New Title"
        assert result.article_content == "New Content"

    def test_update_article_unauthorized(self):
        fake_article = create_test_article(article_author_id=1)
        self.mock_article_repo.get_by_id.return_value = fake_article
        fake_account = create_test_account(account_id=99, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            title="Hacked Title",
            content="Hacked Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.save.assert_not_called()
        assert result == "Unauthorized : You are not the author of this article."

    def test_update_article_insufficient_role(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=1,
            user_id=fake_account.account_id,
            title="Hacked Title",
            content="Hacked Content",
        )

        self.mock_article_repo.get_by_id.assert_not_called()
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.save.assert_not_called()
        assert result == "Insufficient permissions."

    def test_update_article_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None
        fake_account = create_test_account(account_role=AccountRole.AUTHOR)
        self.mock_account_repo.get_by_id.return_value = fake_account

        result = self.service.update_article(
            article_id=999,
            user_id=fake_account.account_id,
            title="New Title",
            content="New Content",
        )

        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.save.assert_not_called()
        assert result == "Article not found."


class TestDeleteArticle(ArticleServiceTestBase):
    def test_delete_article_success_by_author(self):
        fake_article = create_test_article(article_id=1, article_author_id=1)
        fake_account = create_test_account(account_id=1, account_role=AccountRole.AUTHOR)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_called_once_with(fake_article)
        assert result is True

    def test_delete_article_success_by_admin(self):
        fake_article = create_test_article(article_id=1, article_author_id=1)
        fake_admin = create_test_account(account_id=99, account_role=AccountRole.ADMIN)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_admin
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_admin.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_admin.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_called_once_with(fake_article)
        assert result is True

    def test_delete_article_unauthorized_ownership(self):
        fake_article = create_test_article(article_author_id=1)
        fake_author_other = create_test_account(account_id=99, account_role=AccountRole.AUTHOR)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_id.return_value = fake_author_other
        result = self.service.delete_article(article_id=fake_article.article_id, user_id=fake_author_other.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_author_other.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_article_repo.delete.assert_not_called()
        assert result == "Unauthorized : Only authors or admins can delete articles."

    def test_delete_article_not_found(self):
        fake_account = create_test_account(account_role=AccountRole.AUTHOR)
        self.mock_article_repo.get_by_id.return_value = None
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.delete_article(article_id=999, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.delete.assert_not_called()
        assert result == "Article not found."


class TestGetAuthorName(ArticleServiceTestBase):
    def test_get_author_name_found(self):
        fake_account = create_test_account(account_username="KingArthur")
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.get_author_name(author_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        assert result == "KingArthur"

    def test_get_author_name_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None
        result = self.service.get_author_name(author_id=999)
        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        assert result == "Unknown"


class TestGetArticleWithComments(ArticleServiceTestBase):
    def test_get_article_with_comments_success(self):
        article_author_id = 10
        comment_author_id = 20
        fake_article = create_test_article(article_id=1, article_author_id=article_author_id)
        fake_comment = create_test_comment(comment_id=101, comment_article_id=1, comment_written_account_id=comment_author_id)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_comment_repo.get_all_by_article_id.return_value = [fake_comment]

        fake_accounts = [
            create_test_account(account_id=article_author_id, account_username="ArticleAuthor"),
            create_test_account(account_id=comment_author_id, account_username="CommentAuthor")
        ]

        self.mock_account_repo.get_by_ids.return_value = fake_accounts
        result = self.service.get_article_with_comments(article_id=1)
        assert not isinstance(result, str)
        assert result.article_with_author.article.article_id == 1
        assert result.article_with_author.author_name == "ArticleAuthor"
        assert "root" in result.threaded_comments.threads
        root_comments = result.threaded_comments.threads["root"]
        assert len(root_comments) == 1
        assert root_comments[0].comment.comment_id == 101
        assert root_comments[0].author_name == "CommentAuthor"
        self.mock_article_repo.get_by_id.assert_called_once_with(1)
        self.mock_comment_repo.get_all_by_article_id.assert_called_once_with(1)
        called_author_ids = self.mock_account_repo.get_by_ids.call_args[0][0]
        assert set(called_author_ids) == {article_author_id, comment_author_id}

    def test_get_article_with_comments_article_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None
        result = self.service.get_article_with_comments(article_id=999)
        assert result == "Article not found."

    def test_get_article_with_comments_unknown_author(self):
        fake_article = create_test_article(article_id=1, article_author_id=999)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_comment_repo.get_all_by_article_id.return_value = []
        self.mock_account_repo.get_by_ids.return_value = []
        result = self.service.get_article_with_comments(article_id=1)
        assert not isinstance(result, str)
        assert result.article_with_author.author_name == "Unknown"
        self.mock_account_repo.get_by_ids.assert_called_once()
