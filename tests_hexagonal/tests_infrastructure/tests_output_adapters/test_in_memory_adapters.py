from datetime import datetime

from src.application.domain.account import Account, AccountRole
from src.application.domain.article import Article
from src.application.domain.comment import Comment
from src.infrastructure.output_adapters.in_memory.account_repository import InMemoryAccountRepository
from src.infrastructure.output_adapters.in_memory.account_session_repository import InMemoryAccountSessionRepository
from src.infrastructure.output_adapters.in_memory.article_repository import InMemoryArticleRepository
from src.infrastructure.output_adapters.in_memory.comment_repository import InMemoryCommentRepository


class TestInMemoryArticleRepository:
    def test_save_new_article(self):
        repo = InMemoryArticleRepository()
        article = Article(0, 1, "Title", "Content", datetime.now())
        repo.save(article)
        assert article.article_id == 1
        assert repo.count_all() == 1
        assert repo.get_by_id(1) == article

    def test_save_existing_article(self):
        repo = InMemoryArticleRepository()
        article = Article(5, 1, "Title", "Content", datetime.now())
        repo.save(article)
        assert article.article_id == 5
        assert repo.get_by_id(5) == article
        article.article_title = "New Title"
        repo.save(article)
        assert repo.get_by_id(5).article_title == "New Title"
        assert repo.count_all() == 1

    def test_delete_article(self):
        repo = InMemoryArticleRepository()
        article = Article(1, 1, "T", "C", datetime.now())
        repo.save(article)
        repo.delete(article)
        assert repo.get_by_id(1) is None
        assert repo.count_all() == 0

    def test_get_all_ordered_and_paginated(self):
        repo = InMemoryArticleRepository()
        account_1 = Article(1, 1, "A1", "C", datetime(2023, 1, 1))
        account_2 = Article(2, 1, "A2", "C", datetime(2023, 1, 3))
        account_3 = Article(3, 1, "A3", "C", datetime(2023, 1, 2))
        repo.save(account_1)
        repo.save(account_2)
        repo.save(account_3)
        ordered = repo.get_all_ordered_by_date_desc()
        assert [articles.article_id for articles in ordered] == [2, 3, 1]
        paginated = repo.get_paginated(1, 2)
        assert [articles.article_id for articles in paginated] == [2, 3]

    def test_get_by_id_not_found(self):
        repo = InMemoryArticleRepository()
        assert repo.get_by_id(999) is None

    def test_delete_nonexistent_article(self):
        repo = InMemoryArticleRepository()
        ghost = Article(999, 1, "Ghost", "C", datetime.now())
        repo.delete(ghost)
        assert repo.count_all() == 0

    def test_get_paginated_out_of_range(self):
        repo = InMemoryArticleRepository()
        repo.save(Article(1, 1, "A1", "C", datetime.now()))
        assert repo.get_paginated(page=99, per_page=10) == []

    def test_auto_increment_after_multiple_saves(self):
        repo = InMemoryArticleRepository()
        account_1 = Article(0, 1, "A1", "C", datetime.now())
        account_2 = Article(0, 1, "A2", "C", datetime.now())
        account_3 = Article(0, 1, "A3", "C", datetime.now())
        repo.save(account_1)
        repo.save(account_2)
        repo.save(account_3)
        assert account_1.article_id == 1
        assert account_2.article_id == 2
        assert account_3.article_id == 3
        assert repo.count_all() == 3


class TestInMemoryAccountRepository:
    def test_save_new_account(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        assert account.account_id == 1
        assert repo.get_by_id(1) == account

    def test_find_by_username_and_email(self):
        repo = InMemoryAccountRepository()
        account = Account(1, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        assert repo.find_by_username("user") == account
        assert repo.find_by_username("notfound") is None
        assert repo.find_by_email("em") == account
        assert repo.find_by_email("notfound") is None

    def test_get_by_ids(self):
        repo = InMemoryAccountRepository()
        account_1 = Account(1, "user1", "pass", "em1", AccountRole.USER, datetime.now())
        account_2 = Account(2, "user2", "pass", "em2", AccountRole.USER, datetime.now())
        repo.save(account_1)
        repo.save(account_2)
        found = repo.get_by_ids([1, 3])
        assert len(found) == 1
        assert found[0].account_id == 1

    def test_get_by_id_not_found(self):
        repo = InMemoryAccountRepository()
        assert repo.get_by_id(999) is None

    def test_get_by_ids_empty_list(self):
        repo = InMemoryAccountRepository()
        repo.save(Account(1, "user", "pass", "em", AccountRole.USER, datetime.now()))
        assert repo.get_by_ids([]) == []


class TestInMemoryCommentRepository:
    def test_save_and_get(self):
        repo = InMemoryCommentRepository()
        comment = Comment(0, 10, 5, None, "content", datetime.now())
        repo.save(comment)
        assert comment.comment_id == 1
        assert repo.get_by_id(1) == comment

    def test_get_all_by_article_id(self):
        repo = InMemoryCommentRepository()
        comment_1 = Comment(1, 10, 5, None, "c1", datetime.now())
        comment_2 = Comment(2, 20, 5, None, "c2", datetime.now())
        comment_3 = Comment(3, 10, 5, None, "c3", datetime.now())
        repo.save(comment_1)
        repo.save(comment_2)
        repo.save(comment_3)
        found = repo.get_all_by_article_id(10)
        assert len(found) == 2
        assert {comments.comment_id for comments in found} == {1, 3}

    def test_delete(self):
        repo = InMemoryCommentRepository()
        comment = Comment(1, 10, 5, None, "content", datetime.now())
        repo.save(comment)
        repo.delete(comment.comment_id)
        assert repo.get_by_id(1) is None

    def test_get_all_by_article_id_empty(self):
        repo = InMemoryCommentRepository()
        assert repo.get_all_by_article_id(999) == []

    def test_delete_nonexistent_comment(self):
        repo = InMemoryCommentRepository()
        repo.delete(999)
        assert repo.get_by_id(999) is None


class TestInMemoryAccountSessionRepository:
    def test_store_and_retrieve(self):
        repo = InMemoryAccountSessionRepository()
        repo.store_value("user_id", 42)
        assert repo.retrieve_value("user_id") == 42
        assert repo.retrieve_value("notfound") is None

    def test_invalidate(self):
        repo = InMemoryAccountSessionRepository()
        repo.store_value("user_id", 42)
        repo.invalidate()
        assert repo.retrieve_value("user_id") is None

    def test_overwrite_existing_key(self):
        repo = InMemoryAccountSessionRepository()
        repo.store_value("role", "user")
        repo.store_value("role", "admin")
        assert repo.retrieve_value("role") == "admin"
