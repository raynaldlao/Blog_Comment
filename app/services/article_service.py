from sqlalchemy import select
from sqlalchemy.orm import defer, joinedload

from app.models import Article
from database.database_setup import db_session


class ArticleService:
    @staticmethod
    def get_all_ordered_by_date():
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
        query = select(Article).where(Article.article_id == article_id).options(joinedload(Article.article_author))
        return db_session.execute(query).unique().scalar_one_or_none()

    @staticmethod
    def create_article(title, content, author_id):
        new_article = Article(article_title=title, article_content=content, article_author_id=author_id)
        db_session.add(new_article)
        db_session.commit()
        return True

    @staticmethod
    def update_article(article_id, user_id, role, title, content):
        article = db_session.get(Article, article_id)
        if not article or (role != "admin" and article.article_author_id != user_id):
            return False

        article.article_title = title
        article.article_content = content
        db_session.commit()
        return True

    @staticmethod
    def delete_article(article_id, user_id, role):
        article = db_session.get(Article, article_id)
        if not article or (role != "admin" and article.article_author_id != user_id):
            return False

        db_session.delete(article)
        db_session.commit()
        return True
