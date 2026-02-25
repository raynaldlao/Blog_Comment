from sqlalchemy import select
from sqlalchemy.orm import Session, defer, joinedload, selectinload

from app.models import Article, Comment
from database.database_setup import database_engine


class ArticleService:
    @staticmethod
    def get_all_ordered_by_date():
        with Session(database_engine) as db_session:
            query = (
                select(Article)
                .options(
                    joinedload(Article.article_author),
                    defer(Article.article_content),
                )
                .order_by(Article.article_published_at.desc())
            )
            return db_session.execute(query).unique().scalars().all()

    @staticmethod
    def get_by_id(article_id):
        with Session(database_engine) as db_session:
            query = (
                select(Article)
                .where(Article.article_id == article_id)
                .options(
                    joinedload(Article.article_author),
                    selectinload(Article.article_comments).options(joinedload(Comment.comment_author), selectinload(Comment.comment_replies).options(joinedload(Comment.comment_author))),
                )
            )
            return db_session.execute(query).unique().scalar_one_or_none()

    @staticmethod
    def create_article(title, content, author_id):
        with Session(database_engine) as db_session:
            new_article = Article(article_title=title, article_content=content, article_author_id=author_id)
            db_session.add(new_article)
            db_session.commit()
            return True

    @staticmethod
    def update_article(article_id, user_id, role, title, content):
        with Session(database_engine) as db_session:
            article = db_session.get(Article, article_id)
            if not article:
                return False
            if role != "admin" and article.article_author_id != user_id:
                return False

            article.article_title = title
            article.article_content = content
            db_session.commit()
            return True

    @staticmethod
    def delete_article(article_id, user_id, role):
        with Session(database_engine) as db_session:
            article = db_session.get(Article, article_id)
            if not article:
                return False
            if role != "admin" and article.article_author_id != user_id:
                return False

            db_session.delete(article)
            db_session.commit()
            return True
