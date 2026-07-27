from datetime import datetime

import pytest

from src.application.domain.account import Account, AccountRole
from src.application.domain.article import Article
from src.application.domain.comment import Comment
from src.application.domain.uploaded_file import UploadedFile
from src.infrastructure.output_adapters.in_memory.account_repository import InMemoryAccountRepository
from src.infrastructure.output_adapters.in_memory.account_session_repository import InMemoryAccountSessionRepository
from src.infrastructure.output_adapters.in_memory.article_repository import InMemoryArticleRepository
from src.infrastructure.output_adapters.in_memory.comment_repository import InMemoryCommentRepository
from src.infrastructure.output_adapters.in_memory.file_storage_repository import InMemoryFileStorageRepository
from src.infrastructure.output_adapters.in_memory.password_hasher_repository import InMemoryPasswordHasherRepository


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
        fetched_article = repo.get_by_id(5)
        assert fetched_article is not None
        assert fetched_article.article_title == "New Title"
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

    def test_search_by_title(self):
        repo = InMemoryArticleRepository()
        repo.save(Article(1, 1, "Learning BlockNote", "Content", datetime(2023, 1, 3)))
        repo.save(Article(2, 1, "Python Tips", "Some python content", datetime(2023, 1, 2)))
        repo.save(Article(3, 1, "Advanced BlockNote", "More content", datetime(2023, 1, 1)))
        results = repo.search("BlockNote", page=1, per_page=10)
        assert len(results) == 2
        assert [a.article_id for a in results] == [1, 3]

    def test_search_by_description(self):
        repo = InMemoryArticleRepository()
        repo.save(Article(1, 1, "Title A", "Content", datetime(2023, 1, 2), article_description="This is a great tutorial"))
        repo.save(Article(2, 1, "Title B", "Content", datetime(2023, 1, 1)))
        results = repo.search("tutorial", page=1, per_page=10)
        assert len(results) == 1
        assert results[0].article_id == 1

    def test_search_count(self):
        repo = InMemoryArticleRepository()
        repo.save(Article(1, 1, "Python Guide", "Learn python", datetime(2023, 1, 3)))
        repo.save(Article(2, 1, "JS Guide", "Learn javascript", datetime(2023, 1, 2)))
        repo.save(Article(3, 1, "Rust Guide", "Learn rust", datetime(2023, 1, 1)))
        assert repo.count_search("Guide") == 3
        assert repo.count_search("Python") == 1
        assert repo.count_search("Nonexistent") == 0

    def test_search_no_match(self):
        repo = InMemoryArticleRepository()
        repo.save(Article(1, 1, "Title", "Content", datetime.now()))
        assert repo.search("xyznonexistent", page=1, per_page=10) == []

    def test_search_by_author_username(self):
        account_repository = InMemoryAccountRepository()

        author_account = Account(
            1, "john_doe", "hashed_password", "john@test.com",
            AccountRole.AUTHOR, datetime(2023, 1, 1),
        )

        account_repository.save(author_account)

        article_repository = InMemoryArticleRepository(
            account_repository=account_repository,
        )

        article_repository.save(Article(
            1, 1, "Python Tips", "Content", datetime(2023, 1, 2),
        ))

        article_repository.save(Article(
            2, 2, "JS Guide", "Content", datetime(2023, 1, 1),
        ))

        search_results = article_repository.search("john", page=1, per_page=10)
        assert len(search_results) == 1
        assert search_results[0].article_id == 1

    def test_search_by_author_username_no_match(self):
        account_repository = InMemoryAccountRepository()
        author_account = Account(
            1, "john_doe", "hashed_password", "john@test.com",
            AccountRole.AUTHOR, datetime(2023, 1, 1),
        )

        account_repository.save(author_account)

        article_repository = InMemoryArticleRepository(
            account_repository=account_repository,
        )

        article_repository.save(Article(
            1, 1, "Python Tips", "Content", datetime(2023, 1, 2),
        ))

        search_results = article_repository.search("nonexistent", page=1, per_page=10)
        assert search_results == []

    def test_search_by_author_username_returns_all_matching_articles(self):
        account_repository = InMemoryAccountRepository()

        author_account = Account(
            1, "john_doe", "hashed_password", "john@test.com",
            AccountRole.AUTHOR, datetime(2023, 1, 1),
        )

        account_repository.save(author_account)

        article_repository = InMemoryArticleRepository(
            account_repository=account_repository,
        )

        article_repository.save(Article(
            1, 1, "Python Tips", "Content", datetime(2023, 1, 3),
        ))

        article_repository.save(Article(
            2, 1, "Rust Guide", "Content", datetime(2023, 1, 2),
        ))

        article_repository.save(Article(
            3, 1, "JS Notes", "Content", datetime(2023, 1, 1),
        ))

        search_results = article_repository.search("john", page=1, per_page=10)
        assert len(search_results) == 3

    def test_count_search_by_author_username(self):
        account_repository = InMemoryAccountRepository()
        author_account = Account(
            1, "john_doe", "hashed_password", "john@test.com",
            AccountRole.AUTHOR, datetime(2023, 1, 1),
        )
        account_repository.save(author_account)

        article_repository = InMemoryArticleRepository(
            account_repository=account_repository,
        )
        article_repository.save(Article(
            1, 1, "Python Tips", "Content", datetime(2023, 1, 2),
        ))
        article_repository.save(Article(
            2, 2, "JS Guide", "Content", datetime(2023, 1, 1),
        ))

        assert article_repository.count_search("john") == 1
        assert article_repository.count_search("python") == 1
        assert article_repository.count_search("nonexistent") == 0


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

    def test_get_all_accounts(self):
        repo = InMemoryAccountRepository()
        a1 = Account(1, "user1", "pass", "em1", AccountRole.USER, datetime.now())
        a2 = Account(2, "user2", "pass", "em2", AccountRole.USER, datetime.now())
        repo.save(a1)
        repo.save(a2)
        results = repo.get_all()
        assert len(results) == 2
        assert a1 in results
        assert a2 in results

    def test_get_all_paginated_page_1(self):
        repo = InMemoryAccountRepository()
        for i in range(5):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime(2024, 1, 1, 0, 0, i)))
        results = repo.get_all_paginated(page=1, per_page=2)
        assert len(results) == 2
        assert results[0].account_username == "user4"
        assert results[1].account_username == "user3"

    def test_get_all_paginated_page_2(self):
        repo = InMemoryAccountRepository()
        for i in range(5):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime(2024, 1, 1, 0, 0, i)))
        results = repo.get_all_paginated(page=2, per_page=2)
        assert len(results) == 2
        assert results[0].account_username == "user2"
        assert results[1].account_username == "user1"

    def test_get_all_paginated_empty_page(self):
        repo = InMemoryAccountRepository()
        for i in range(3):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime(2024, 1, 1, 0, 0, i)))
        results = repo.get_all_paginated(page=2, per_page=3)
        assert len(results) == 0

    def test_count_all_accounts(self):
        repo = InMemoryAccountRepository()
        assert repo.count_all() == 0
        repo.save(Account(0, "u1", "p", "e1@t.com", AccountRole.USER, datetime.now()))
        repo.save(Account(0, "u2", "p", "e2@t.com", AccountRole.USER, datetime.now()))
        assert repo.count_all() == 2

    def test_search_accounts_by_username(self):
        repo = InMemoryAccountRepository()
        for i in range(5):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime(2024, 1, 1, 0, 0, i)))
        results = repo.search("user3", page=1, per_page=10)
        assert len(results) == 1
        assert results[0].account_username == "user3"

    def test_search_accounts_by_email(self):
        repo = InMemoryAccountRepository()
        for i in range(5):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime(2024, 1, 1, 0, 0, i)))
        results = repo.search("@t.com", page=1, per_page=10)
        assert len(results) == 5

    def test_search_accounts_no_match(self):
        repo = InMemoryAccountRepository()
        repo.save(Account(0, "user1", "pass", "em1@t.com", AccountRole.USER, datetime.now()))
        results = repo.search("zzz", page=1, per_page=10)
        assert len(results) == 0

    def test_search_accounts_count(self):
        repo = InMemoryAccountRepository()
        for i in range(5):
            repo.save(Account(0, f"user{i}", "pass", f"em{i}@t.com", AccountRole.USER, datetime.now()))
        assert repo.count_search("user") == 5
        assert repo.count_search("zzz") == 0

    def test_update_email_changes_email(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "old@test.com", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_email(account.account_id, "new@test.com")
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.account_email == "new@test.com"

    def test_update_password_changes_password(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "old_hash", "e@t.com", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_password(account.account_id, "new_hash")
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.account_password == "new_hash"

    def test_delete_account(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        assert repo.get_by_id(account.account_id) is not None
        repo.delete(account.account_id)
        assert repo.get_by_id(account.account_id) is None

    def test_delete_nonexistent_account_does_not_raise(self):
        repo = InMemoryAccountRepository()
        repo.delete(999)

    def test_update_ban_status_ban(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_ban_status(account.account_id, True, "Spam")
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.is_banned is True
        assert updated.ban_reason == "Spam"

    def test_update_ban_status_unban(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_ban_status(account.account_id, True, "Spam")
        repo.update_ban_status(account.account_id, False, None)
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.is_banned is False
        assert updated.ban_reason is None

    def test_update_session_token_sets_token(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_session_token(account.account_id, "abc123")
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.session_token == "abc123"

    def test_update_session_token_clears_token(self):
        repo = InMemoryAccountRepository()
        account = Account(0, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save(account)
        repo.update_session_token(account.account_id, "abc123")
        repo.update_session_token(account.account_id, None)
        updated = repo.get_by_id(account.account_id)
        assert updated is not None
        assert updated.session_token is None

    def test_update_session_token_nonexistent_account_raises(self):
        from blog_exceptions import AccountNotFoundError

        repo = InMemoryAccountRepository()
        with pytest.raises(AccountNotFoundError, match="not found"):
            repo.update_session_token(999, "abc123")


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

    def test_get_by_account_id(self):
        repo = InMemoryCommentRepository()
        c1 = Comment(1, 10, 5, None, "c1", datetime.now())
        c2 = Comment(2, 10, 5, None, "c2", datetime.now())
        c3 = Comment(3, 10, 6, None, "c3", datetime.now())
        repo.save(c1)
        repo.save(c2)
        repo.save(c3)
        found = repo.get_by_account_id(5)
        assert len(found) == 2
        assert all(c.comment_written_account_id == 5 for c in found)

    def test_get_by_account_id_empty(self):
        repo = InMemoryCommentRepository()
        assert repo.get_by_account_id(999) == []


class TestInMemoryAccountSessionRepository:
    def test_store_and_retrieve(self):
        repo = InMemoryAccountSessionRepository()
        account = Account(1, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save_account(account)
        assert repo.get_account() == account

    def test_invalidate(self):
        repo = InMemoryAccountSessionRepository()
        account = Account(1, "user", "pass", "em", AccountRole.USER, datetime.now())
        repo.save_account(account)
        repo.clear()
        assert repo.get_account() is None

    def test_overwrite_existing_account(self):
        repo = InMemoryAccountSessionRepository()
        account1 = Account(1, "user1", "pass", "em", AccountRole.USER, datetime.now())
        account2 = Account(2, "user2", "pass", "em", AccountRole.ADMIN, datetime.now())
        repo.save_account(account1)
        repo.save_account(account2)
        assert repo.get_account() == account2

    def test_get_account_empty_returns_none(self):
        repo = InMemoryAccountSessionRepository()
        assert repo.get_account() is None


class TestInMemoryFileStorageRepository:
    def test_save_and_get(self):
        repo = InMemoryFileStorageRepository()
        uploaded_file = UploadedFile(
            file_id="abc-123", original_filename="test.png",
            mime_type="image/png", size=1024, data=b"png-data",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        saved = repo.save(uploaded_file)
        assert saved == uploaded_file
        retrieved = repo.get("abc-123")
        assert retrieved == uploaded_file

    def test_get_nonexistent(self):
        repo = InMemoryFileStorageRepository()
        assert repo.get("nonexistent-id") is None

    def test_delete(self):
        repo = InMemoryFileStorageRepository()
        uploaded_file = UploadedFile(
            file_id="to-delete", original_filename="del.png",
            mime_type="image/png", size=512, data=b"del",
        )
        repo.save(uploaded_file)
        repo.delete("to-delete")
        assert repo.get("to-delete") is None

    def test_delete_nonexistent_idempotent(self):
        repo = InMemoryFileStorageRepository()
        repo.delete("does-not-exist")


class TestInMemoryPasswordHasherRepository:
    def test_hash_and_verify(self):
        repo = InMemoryPasswordHasherRepository()
        hashed = repo.hash("secure_password")
        assert repo.verify("secure_password", hashed) is True

    def test_verify_wrong_password(self):
        repo = InMemoryPasswordHasherRepository()
        hashed = repo.hash("correct_password")
        assert repo.verify("wrong_password", hashed) is False

    def test_check_needs_rehash_returns_false(self):
        repo = InMemoryPasswordHasherRepository()
        hashed = repo.hash("any_password")
        assert repo.check_needs_rehash(hashed) is False
