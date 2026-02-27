from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.article_model import Article
from app.models.comment_model import Comment
from database.database_setup import db_session


class CommentService:
    @staticmethod
    def create_reply(parent_comment_id, user_id, content):
        parent = db_session.get(Comment, parent_comment_id)
        if not parent:
            return None

        actual_parent_id = parent.comment_reply_to if parent.comment_reply_to else parent.comment_id
        new_reply = Comment(
            comment_article_id=parent.comment_article_id,
            comment_written_account_id=user_id,
            comment_content=content,
            comment_reply_to=actual_parent_id
        )
        db_session.add(new_reply)
        return parent.comment_article_id

    @staticmethod
    def get_by_id(comment_id):
        query = select(Comment).options(joinedload(Comment.comment_author)).where(Comment.comment_id == comment_id)
        return db_session.execute(query).unique().scalar_one_or_none()

    @staticmethod
    def create_comment(article_id, user_id, content):
        article = db_session.get(Article, article_id)
        if not article:
            return False
        new_comment = Comment(comment_article_id=article_id, comment_written_account_id=user_id, comment_content=content)
        db_session.add(new_comment)
        return True

    @staticmethod
    def delete_comment(comment_id, role):
        if role != "admin":
            return False
        comment = db_session.get(Comment, comment_id)
        if not comment:
            return False
        article_id = comment.comment_article_id
        db_session.delete(comment)
        return article_id

    @staticmethod
    def get_tree_by_article_id(article_id):
        query = select(Comment).where(Comment.comment_article_id == article_id).options(joinedload(Comment.comment_author)).order_by(Comment.comment_posted_at.asc())
        all_comments = db_session.execute(query).unique().scalars().all()
        return [c for c in all_comments if c.comment_reply_to is None]
