from sqlalchemy.orm import Session

from src.application.domain.comment import Comment
from src.application.output_ports.comment_repository import CommentRepository
from src.infrastructure.output_adapters.dto.comment_record import CommentRecord
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_base_adapter import (
    SqlAlchemyBaseAdapter,
)


class SqlAlchemyCommentAdapter(SqlAlchemyBaseAdapter, CommentRepository):
    """
    SQLAlchemy-based implementation of the CommentRepository port.

    This adapter manages the persistence and retrieval of Comment domain entities
    using SQLAlchemy ORM and the database.

    All methods may raise DatabaseError on database failure.
    """

    def __init__(self, session: Session):
        """
        Initializes the adapter with a SQLAlchemy session.

        Args:
            session (Session): An active SQLAlchemy database session.
        """
        super().__init__(session)

    def _to_domain(self, model: CommentModel) -> Comment:
        """
        Maps a SQLAlchemy ORM model to a Domain Entity via a DTO.

        Args:
            model (CommentModel): The database record to convert.

        Returns:
            Comment: The converted Domain Entity.
        """
        record = CommentRecord.model_validate(model)
        return record.to_domain()

    def save(self, comment: Comment) -> None:
        """
        Saves a new comment or updates an existing one in the database.
        If the comment has a valid positive ID, an UPDATE is performed.
        Otherwise, a new record is INSERTed.

        Args:
            comment (Comment): The domain Comment entity to persist.
        """
        if comment.comment_id and comment.comment_id > 0:
            self._db_query_raw(
                lambda: self._session.query(CommentModel).filter_by(
                    comment_id=comment.comment_id,
                ).update({
                CommentModel.comment_article_id: comment.comment_article_id,
                CommentModel.comment_written_account_id: comment.comment_written_account_id,
                CommentModel.comment_reply_to: comment.comment_reply_to,
                CommentModel.comment_content: comment.comment_content,
                CommentModel.is_deleted: comment.is_deleted,
                CommentModel.deleted_at: comment.deleted_at,
                CommentModel.edited_at: comment.edited_at,
                CommentModel.deleted_by: comment.deleted_by,
                })
            )
            self._db_commit()
            return

        model = CommentModel()
        self._db_add(model)
        model.comment_article_id = comment.comment_article_id
        model.comment_written_account_id = comment.comment_written_account_id
        model.comment_reply_to = comment.comment_reply_to
        model.comment_content = comment.comment_content
        model.is_deleted = comment.is_deleted
        model.deleted_at = comment.deleted_at
        model.edited_at = comment.edited_at
        model.deleted_by = comment.deleted_by
        self._db_commit()

    def get_by_id(self, comment_id: int) -> Comment | None:
        """
        Retrieves a single comment by its ID.

        Args:
            comment_id (int): The unique identifier of the comment.

        Returns:
            Comment | None: The Comment domain entity if found, None otherwise.
        """
        model = self._db_get(CommentModel, comment_id)
        if model is None:
            return None
        return self._to_domain(model)

    def get_all_by_article_id(self, article_id: int) -> list[Comment]:
        """
        Retrieves all comments associated with a specific article.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            list[Comment]: A list of Comment domain entities.
        """
        models = self._db_query_all(CommentModel, comment_article_id=article_id)
        return [self._to_domain(model) for model in models]

    def get_by_reply_to(self, comment_id: int) -> list[Comment]:
        """
        Retrieves all direct child comments that reply to a given comment.

        Args:
            comment_id (int): ID of the parent comment.

        Returns:
            list[Comment]: A list of direct child Comment domain entities.
        """
        models = self._db_query_all(CommentModel, comment_reply_to=comment_id)
        return [self._to_domain(model) for model in models]

    def get_by_account_id(self, account_id: int) -> list[Comment]:
        """
        Retrieves all comments authored by a specific account.

        Args:
            account_id (int): ID of the account.

        Returns:
            list[Comment]: A list of Comment domain entities for this author.
        """
        models = self._db_query_all(CommentModel, comment_written_account_id=account_id)
        return [self._to_domain(model) for model in models]

    def delete(self, comment_id: int) -> None:
        """
        Deletes a comment by its ID from the repository.

        Args:
            comment_id (int): The unique identifier of the comment to delete.
        """
        self._db_query_raw(
            lambda: self._session.query(CommentModel).filter_by(
                comment_id=comment_id,
            ).delete()
        )
        self._db_commit()
