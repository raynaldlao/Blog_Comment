from datetime import datetime

from src.application.domain.article import Article
from src.infrastructure.output_adapters.dto.article_record import ArticleRecord


class TestArticleRecordCreation:
    def test_create_record_with_valid_data(self):
        record = ArticleRecord(
            article_id=1,
            article_author_id=10,
            article_title="Test Title",
            article_content="Test Content",
            article_published_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        assert record.article_id == 1
        assert record.article_title == "Test Title"

    def test_create_record_from_object_attributes(self):
        class MockArticleModel:
            def __init__(self):
                self.article_id = 99
                self.article_author_id = 42
                self.article_title = "ORM Title"
                self.article_content = "ORM Content"
                self.article_published_at = datetime(2023, 1, 1, 12, 0, 0)

        record = ArticleRecord.model_validate(MockArticleModel())
        assert record.article_id == 99
        assert record.article_title == "ORM Title"


class TestArticleRecordToDomain:
    def test_to_domain_returns_article_instance(self):
        record = ArticleRecord(
            article_id=1,
            article_author_id=10,
            article_title="Domain Test",
            article_content="Content",
            article_published_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        domain = record.to_domain()
        assert isinstance(domain, Article)

    def test_to_domain_maps_all_fields_correctly(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        record = ArticleRecord(
            article_id=5,
            article_author_id=8,
            article_title="Mapped",
            article_content="Properly",
            article_published_at=dt,
        )
        domain = record.to_domain()
        assert domain.article_id == 5
        assert domain.article_author_id == 8
        assert domain.article_title == "Mapped"
        assert domain.article_content == "Properly"
        assert domain.article_published_at == dt
