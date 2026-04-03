from datetime import datetime

from src.application.domain.comment import Comment
from src.infrastructure.output_adapters.dto.comment_record import CommentRecord


class TestCommentRecordCreation:
    def test_create_record_with_valid_data(self):
        record = CommentRecord(
            comment_id=1,
            comment_article_id=10,
            comment_written_account_id=5,
            comment_reply_to=None,
            comment_content="Test Content",
            comment_posted_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        assert record.comment_id == 1
        assert record.comment_content == "Test Content"
        assert record.comment_reply_to is None

    def test_create_record_from_object_attributes(self):
        class MockCommentModel:
            def __init__(self):
                self.comment_id = 99
                self.comment_article_id = 42
                self.comment_written_account_id = 21
                self.comment_reply_to = 5
                self.comment_content = "ORM Content"
                self.comment_posted_at = datetime(2023, 1, 1, 12, 0, 0)

        record = CommentRecord.model_validate(MockCommentModel())
        assert record.comment_id == 99
        assert record.comment_content == "ORM Content"
        assert record.comment_reply_to == 5


class TestCommentRecordToDomain:
    def test_to_domain_returns_comment_instance(self):
        record = CommentRecord(
            comment_id=1,
            comment_article_id=10,
            comment_written_account_id=5,
            comment_reply_to=None,
            comment_content="Content",
            comment_posted_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        domain = record.to_domain()
        assert isinstance(domain, Comment)

    def test_to_domain_maps_all_fields_correctly(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        record = CommentRecord(
            comment_id=5,
            comment_article_id=8,
            comment_written_account_id=3,
            comment_reply_to=1,
            comment_content="Mapped",
            comment_posted_at=dt,
        )
        domain = record.to_domain()
        assert domain.comment_id == 5
        assert domain.comment_article_id == 8
        assert domain.comment_written_account_id == 3
        assert domain.comment_reply_to == 1
        assert domain.comment_content == "Mapped"
        assert domain.comment_posted_at == dt
