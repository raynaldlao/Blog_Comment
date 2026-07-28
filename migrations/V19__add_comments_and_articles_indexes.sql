CREATE INDEX IF NOT EXISTS idx_comments_article_id
  ON comments (comment_article_id);

CREATE INDEX IF NOT EXISTS idx_comments_account_id
  ON comments (comment_written_account_id);

CREATE INDEX IF NOT EXISTS idx_comments_posted_at
  ON comments (comment_posted_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_published_at
  ON articles (article_published_at DESC);
