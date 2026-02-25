from app.models import Comment


class CommentService:
    @staticmethod
    def get_by_id(db_session, comment_id):
        return db_session.get(Comment, comment_id)

    @staticmethod
    def create_comment(db_session, article_id, user_id, content):
        new_comment = Comment(comment_article_id=article_id, comment_written_account_id=user_id, comment_content=content, comment_reply_to=None)
        db_session.add(new_comment)
        db_session.commit()
        return new_comment

    @staticmethod
    def create_reply(db_session, parent_comment_id, user_id, content):
        parent = db_session.get(Comment, parent_comment_id)
        if not parent:
            return None

        new_reply = Comment(comment_article_id=parent.comment_article_id, comment_written_account_id=user_id, comment_content=content, comment_reply_to=parent_comment_id)
        db_session.add(new_reply)
        db_session.commit()
        return new_reply

    @staticmethod
    def delete_comment(db_session, comment):
        db_session.delete(comment)
        db_session.commit()
