ALTER TABLE comments DROP CONSTRAINT comments_reply_fk;
ALTER TABLE comments ADD CONSTRAINT comments_reply_fk
    FOREIGN KEY (comment_reply_to) REFERENCES comments(comment_id)
    ON DELETE CASCADE;
