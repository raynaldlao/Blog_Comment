from sqlalchemy import func, select
from sqlalchemy.orm import defer, joinedload

from app.models.account_model import Account
from app.models.article_model import Article
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
        return new_article

    @staticmethod
    def update_article(article_id, user_id, role, title, content):
        article = db_session.get(Article, article_id)
        if not article or (role != "admin" and article.article_author_id != user_id):
            return False

        article.article_title = title
        article.article_content = content
        return True

    @staticmethod
    def delete_article(article_id, user_id, role):
        article = db_session.get(Article, article_id)
        if not article or (role != "admin" and article.article_author_id != user_id):
            return False

        db_session.delete(article)
        return True

    @staticmethod
    def get_paginated_articles(page, per_page):
        query = (
            select(
                Article.article_id,
                Article.article_title,
                Article.article_published_at,
                Article.article_author_id,
                Account.account_username
            )
            .join(Account, Article.article_author_id == Account.account_id)
            .order_by(Article.article_published_at.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
        return db_session.execute(query).all()

    @staticmethod
    def get_total_count():
        query = select(func.count(Article.article_id))
        return db_session.execute(query).scalar()
