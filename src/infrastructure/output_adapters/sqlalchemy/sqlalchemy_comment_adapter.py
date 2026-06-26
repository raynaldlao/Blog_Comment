from sqlalchemy.orm import Session

from src.application.domain.comment import Comment
from src.application.output_ports.comment_repository import CommentRepository
from src.infrastructure.output_adapters.dto.comment_record import CommentRecord
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel


class SqlAlchemyCommentAdapter(CommentRepository):
    """
    SQLAlchemy-based implementation of the CommentRepository port.

    This adapter manages the persistence and retrieval of Comment domain entities
    using SQLAlchemy ORM and the database.
    """

    def __init__(self, session: Session):
        """
        Initializes the adapter with a SQLAlchemy session.

        Args:
            session (Session): An active SQLAlchemy database session.
        """
        self._session = session

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
        Saves a new comment or updates an existing one.

        Args:
            comment (Comment): The Comment domain entity to save.
        """
        if comment.comment_id and comment.comment_id > 0:
            self._session.query(CommentModel).filter_by(
                comment_id=comment.comment_id,
            ).update({
                CommentModel.comment_article_id: comment.comment_article_id,
                CommentModel.comment_written_account_id: comment.comment_written_account_id,
                CommentModel.comment_reply_to: comment.comment_reply_to,
                CommentModel.comment_content: comment.comment_content,
            })
            self._session.commit()
            return

        model = CommentModel()
        self._session.add(model)
        model.comment_article_id = comment.comment_article_id
        model.comment_written_account_id = comment.comment_written_account_id
        model.comment_reply_to = comment.comment_reply_to
        model.comment_content = comment.comment_content
        self._session.commit()

    def get_by_id(self, comment_id: int) -> Comment | None:
        """
        Retrieves a single comment by its ID.

        Args:
            comment_id (int): The unique identifier of the comment.

        Returns:
            Comment | None: The Comment domain entity if found, None otherwise.
        """
        model = self._session.get(CommentModel, comment_id)
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
        models = self._session.query(CommentModel).filter_by(comment_article_id=article_id).all()
        return [self._to_domain(model) for model in models]

    def delete(self, comment_id: int) -> None:
        """
        Deletes a comment by its ID from the repository.

        Args:
            comment_id (int): The unique identifier of the comment to delete.
        """
        self._session.query(CommentModel).filter_by(
            comment_id=comment_id,
        ).delete()
        self._session.commit()
