from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.constants import Role
from app.models.article_model import Article
from app.models.comment_model import Comment


class CommentService:
    """
    Service class responsible for business logic operations related to Comments.
    Handles creating top-level comments, replies, retrieving comments by article, and deleting comments.
    """

    def __init__(self, session: Session):
        """
        Initialize the service with a database session (Dependency Injection).
        
        Args:
            session (Session): The SQLAlchemy database session to use for queries.
        """
        self.session = session

    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Optional[int]:
        """
        Creates a reply to an existing comment. A reply is linked either to the parent directly
        or to the parent's top-level comment (threading logic).

        Args:
            parent_comment_id (int): The ID of the comment being replied to.
            user_id (int): The identifier of the user creating the reply.
            content (str): The text content of the reply.

        Returns:
            Optional[int]: The article ID the comment belongs to if successful, None if the parent comment is not found.
        """
        parent = self.session.get(Comment, parent_comment_id)
        if not parent:
            return None

        actual_parent_id = parent.comment_reply_to if parent.comment_reply_to else parent.comment_id
        new_reply = Comment(
            comment_article_id=parent.comment_article_id,
            comment_written_account_id=user_id,
            comment_content=content,
            comment_reply_to=actual_parent_id
        )
        self.session.add(new_reply)
        return parent.comment_article_id

    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """
        Retrieves a single comment by its ID. Eagerly loads the author information.

        Args:
            comment_id (int): The unique identifier of the comment.

        Returns:
            Optional[Comment]: The Comment instance if found, None otherwise.
        """
        query = select(Comment).options(joinedload(Comment.comment_author)).where(Comment.comment_id == comment_id)
        return self.session.execute(query).unique().scalar_one_or_none()

    def create_comment(self, article_id: int, user_id: int, content: str) -> bool:
        """
        Creates a top-level comment on an article.

        Args:
            article_id (int): The ID of the article being commented on.
            user_id (int): The identifier of the user creating the comment.
            content (str): The body text of the comment.

        Returns:
            bool: True if the comment was created successfully, False if the article does not exist.
        """
        article = self.session.get(Article, article_id)
        if not article:
            return False
            
        new_comment = Comment(
            comment_article_id=article_id,
            comment_written_account_id=user_id,
            comment_content=content
        )
        self.session.add(new_comment)
        return True

    def delete_comment(self, comment_id: int, role: str) -> Optional[int]:
        """
        Deletes a comment. Only users with the 'admin' role can delete comments.

        Args:
            comment_id (int): The ID of the comment to delete.
            role (str): The role of the user attempting the deletion.

        Returns:
            Optional[int]: The article ID the comment belonged to if successful, None if unauthorized or not found.
        """
        if role != Role.ADMIN:
            return None
            
        comment = self.session.get(Comment, comment_id)
        if not comment:
            return None
            
        article_id = comment.comment_article_id
        self.session.delete(comment)
        return article_id

    def get_tree_by_article_id(self, article_id: int) -> List[Comment]:
        """
        Retrieves all comments for a specific article as a threaded tree structure.
        Eagerly loads author information and returns only the top-level comments;
        replies are typically nested within the 'replies' relationship of the parent comment.

        Args:
            article_id (int): The ID of the article.

        Returns:
            List[Comment]: A list of top-level Comment instances for the given article.
        """
        query = (
            select(Comment)
            .where(Comment.comment_article_id == article_id)
            .options(joinedload(Comment.comment_author))
            .order_by(Comment.comment_posted_at.asc())
        )
        all_comments = self.session.execute(query).unique().scalars().all()
        return [c for c in all_comments if c.comment_reply_to is None]
