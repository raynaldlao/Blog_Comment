from sqlalchemy import select

from app.models import Article


class ArticleService:
    @staticmethod
    def get_all_ordered_by_date(db_session):
        query = select(Article).order_by(Article.article_published_at.desc())
        return db_session.execute(query).scalars().all()

    @staticmethod
    def get_by_id(db_session, article_id):
        return db_session.get(Article, article_id)

    @staticmethod
    def create_article(db_session, title, content, author_id):
        new_article = Article(article_title=title, article_content=content, article_author_id=author_id)
        db_session.add(new_article)
        db_session.commit()
        return new_article

    @staticmethod
    def update_article(db_session, article, title, content):
        article.article_title = title
        article.article_content = content
        db_session.commit()

    @staticmethod
    def delete_article(db_session, article):
        db_session.delete(article)
        db_session.commit()

    @staticmethod
    def can_user_edit_article(article, user_id, role):
        if not article:
            return False
        return role == "admin" or article.article_author_id == user_id
