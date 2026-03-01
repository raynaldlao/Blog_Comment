from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session, defer, joinedload, scoped_session

from app.constants import Role
from app.models.account_model import Account
from app.models.article_model import Article


class ArticleService:
    """
    Service class responsible for business logic operations related to Articles.
    Handles creating, retrieving, updating and deleting articles as well as pagination logic.
    """

    def __init__(self, session: Session | scoped_session[Session]):
        """
        Initialize the service with a database session (Dependency Injection).
        Supports both standard Session and scoped_session.

        Args:
            session (Session | scoped_session[Session]): The SQLAlchemy database session.
    """
        self.session = session

    def get_all_ordered_by_date(self) -> Sequence[Article]:
        """
        Retrieves all articles ordered by their publication date in descending order.

        Returns:
            Sequence[Article]: A sequence of Article instances.
        """
        query = (
            select(Article)
            .options(
                joinedload(Article.article_author),
                defer(Article.article_content),
            )
            .order_by(Article.article_published_at.desc())
        )
        return self.session.execute(query).unique().scalars().all()

    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article instance if found, None otherwise.
        """
        query = (
            select(Article)
            .where(Article.article_id == article_id)
            .options(joinedload(Article.article_author))
        )
        return self.session.execute(query).unique().scalar_one_or_none()

    def create_article(self, title: str, content: str, author_id: int) -> Article:
        """
        Creates a new article instance.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.

        Returns:
            Article: The newly created Article instance.
        """
        new_article = Article(
            article_title=title,
            article_content=content,
            article_author_id=author_id
        )
        self.session.add(new_article)
        return new_article

    def update_article(
        self,
        article_id: int,
        user_id: int,
        role: str,
        title: str,
        content: str
    ) -> Article | None:
        """
        Updates an existing article ensuring the requester is the original author.

        Args:
            article_id (int): ID of the article to update.
            user_id (int): ID of the user requesting the update.
            role (str): Role of the user requesting the update.
            title (str): New title for the article.
            content (str): New content for the article.

        Returns:
            Article | None: The Article instance or None if unauthorized/not found.
        """
        article = self.get_by_id(article_id)
        if not article or article.article_author_id != user_id:
            return None

        article.article_title = title
        article.article_content = content
        return article

    def delete_article(self, article_id: int, user_id: int, role: str) -> bool:
        """
        Deletes an article. Only the original author or an Admin can delete it.

        Args:
            article_id (int): ID of the article to delete.
            user_id (int): ID of the user requesting deletion.
            role (str): Role of the user requesting deletion.

        Returns:
            bool: True if deleted, False otherwise.
        """

        article = self.get_by_id(article_id)
        if not article:
            return False

        if article.article_author_id == user_id or role == Role.ADMIN:
            self.session.delete(article)
            return True

        return False

    def get_paginated_articles(self, page: int, per_page: int) -> Sequence[Row]:
        """
        Retrieves a paginated list of articles containing specific columns.

        Returns:
            Sequence[Row]: A sequence of SQLAlchemy Row objects containing selected columns.
        """
        query = (
            select(
                Article.article_id,
                Article.article_title,
                Article.article_published_at,
                Article.article_author_id,
                Account.account_username
            )
            .join(Account, Article.article_author_id == Account.account_id)
            .order_by(Article.article_id.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
        return self.session.execute(query).all()

    def get_total_count(self) -> int:
        """
        Retrieves the total number of articles.

        Returns:
            int: The total count.
        """
        query = select(func.count(Article.article_id))
        count = self.session.execute(query).scalar()
        return int(count) if count is not None else 0
