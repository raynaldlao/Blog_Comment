ALTER TABLE accounts
    RENAME COLUMN username TO account_username;

ALTER TABLE accounts
    RENAME COLUMN email TO account_email;

ALTER TABLE accounts
    RENAME COLUMN created_at TO account_created_at;

ALTER TABLE articles
    RENAME COLUMN writer_id TO article_author_id;

ALTER TABLE articles
    RENAME COLUMN title TO article_title;

ALTER TABLE articles
    RENAME COLUMN content TO article_content;

ALTER TABLE articles
    RENAME COLUMN published_at TO article_published_at;

ALTER TABLE articles
    DROP CONSTRAINT articles_writer_id_fkey;

ALTER TABLE articles
    ADD CONSTRAINT articles_author_fk
        FOREIGN KEY (article_author_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE;

ALTER TABLE feedback
    RENAME TO comments;

ALTER TABLE comments
    RENAME COLUMN feedback_id TO comment_id;

ALTER TABLE comments
    RENAME COLUMN article_ref TO comment_article_id;

ALTER TABLE comments
    RENAME COLUMN commenter_id TO comment_written_account_id;

ALTER TABLE comments
    RENAME COLUMN reply_to TO comment_reply_to;

ALTER TABLE comments
    RENAME COLUMN message TO comment_content;

ALTER TABLE comments
    RENAME COLUMN posted_at TO comment_posted_at;

ALTER TABLE comments
    DROP CONSTRAINT feedback_article_ref_fkey;

ALTER TABLE comments
    ADD CONSTRAINT comments_article_fk
        FOREIGN KEY (comment_article_id)
        REFERENCES articles(article_id)
        ON DELETE CASCADE;

ALTER TABLE comments
    DROP CONSTRAINT feedback_commenter_id_fkey;

ALTER TABLE comments
    ADD CONSTRAINT comments_author_fk
        FOREIGN KEY (comment_written_account_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE;

ALTER TABLE comments
    DROP CONSTRAINT feedback_reply_to_fkey;

ALTER TABLE comments
    ADD CONSTRAINT comments_reply_fk
        FOREIGN KEY (comment_reply_to)
        REFERENCES comments(comment_id);
