ALTER TABLE comments
    ALTER COLUMN comment_content TYPE VARCHAR(5000);

ALTER TABLE comments
    ADD CONSTRAINT comment_content_min_length 
    CHECK (char_length(comment_content) >= 1);
