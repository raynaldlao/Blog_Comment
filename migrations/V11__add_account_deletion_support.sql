ALTER TABLE articles DROP CONSTRAINT articles_author_fk;
ALTER TABLE articles ALTER COLUMN article_author_id DROP NOT NULL;
ALTER TABLE articles ADD CONSTRAINT articles_author_fk
    FOREIGN KEY (article_author_id) REFERENCES accounts(account_id)
    ON DELETE SET NULL;

ALTER TABLE comments DROP CONSTRAINT comments_reply_fk;
ALTER TABLE comments ADD CONSTRAINT comments_reply_fk
    FOREIGN KEY (comment_reply_to) REFERENCES comments(comment_id)
    ON DELETE SET NULL;

ALTER TABLE comments DROP CONSTRAINT comments_author_fk;
ALTER TABLE comments ALTER COLUMN comment_written_account_id DROP NOT NULL;
ALTER TABLE comments ADD CONSTRAINT comments_author_fk
    FOREIGN KEY (comment_written_account_id) REFERENCES accounts(account_id)
    ON DELETE SET NULL;
