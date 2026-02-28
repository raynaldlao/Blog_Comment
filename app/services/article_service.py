from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, defer, joinedload

from app.constants import Role
from app.models.account_model import Account
from app.models.article_model import Article


class ArticleService:
    """
    Service class responsible for business logic operations related to Articles.
    Handles creating, retrieving, updating and deleting articles as well as pagination logic.
    """

    def __init__(self, session: Session):
        """
        Initialize the service with a database session (Dependency Injection).
        
        Args:
            session (Session): The SQLAlchemy database session to use for queries.
        """
        self.session = session

    def get_all_ordered_by_date(self) -> List[Article]:
        """
        Retrieves all articles ordered by their publication date in descending order.
        Eagerly loads author information and defers the loading of the full content for performance.

        Returns:
            List[Article]: A list of Article instances containing metadata.
        """
        query = (
            select(Article)
            .options(
                joinedload(Article.article_author),
                defer(Article.article_content),
            )
            .order_by(Article.article_published_at.desc())
        )
        return list(self.session.execute(query).unique().scalars().all())

    def get_by_id(self, article_id: int) -> Optional[Article]:
        """
        Retrieves a single article by its ID. Eagerly loads the author information.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Optional[Article]: The Article instance if found, None otherwise.
        """
        query = select(Article).where(Article.article_id == article_id).options(joinedload(Article.article_author))
        return self.session.execute(query).unique().scalar_one_or_none()

    def create_article(self, title: str, content: str, author_id: int) -> Article:
        """
        Creates a new article and adds it to the database session.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.

        Returns:
            Article: The newly created Article instance.
        """
        new_article = Article(article_title=title, article_content=content, article_author_id=author_id)
        self.session.add(new_article)
        return new_article

    def update_article(self, article_id: int, user_id: int, role: str, title: str, content: str) -> Optional[Article]:
        """
        Updates an existing article ensuring the requester is the original author.

        Args:
            article_id (int): The unique identifier of the article to update.
            user_id (int): The identifier of the user attempting to update.
            role (str): The role of the user.
            title (str): The new title of the article.
            content (str): The new content of the article.

        Returns:
            Optional[Article]: The updated Article instance if successful, None if not found or unauthorized.
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
            article_id (int): The unique identifier of the article to delete.
            user_id (int): The identifier of the user attempting to delete.
            role (str): The role of the user (e.g., 'admin', 'user').

        Returns:
            bool: True if the deletion was successful, False if not found or unauthorized.
        """
        article = self.get_by_id(article_id)
        if not article or (role != Role.ADMIN and article.article_author_id != user_id):
            return False

        self.session.delete(article)
        return True

    def get_paginated_articles(self, page: int, per_page: int) -> List[tuple]:
        """
        Retrieves a paginated list of articles containing limited metadata.

        Args:
            page (int): The current page number to retrieve (1-indexed).
            per_page (int): The number of articles per page.

        Returns:
            List[tuple]: A list of tuples containing (id, title, published_at, author_id, username).
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
        return list(self.session.execute(query).all())

    def get_total_count(self) -> int:
        """
        Retrieves the total number of articles in the database.

        Returns:
            int: The total count of articles.
        """
        query = select(func.count(Article.article_id))
        count = self.session.execute(query).scalar()
        return int(count) if count is not None else 0
