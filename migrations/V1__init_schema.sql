CREATE TABLE accounts (
  account_id SERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  email TEXT,
  role TEXT NOT NULL CHECK (role IN ('author', 'user')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE articles (
  article_id SERIAL PRIMARY KEY,
  writer_id INTEGER NOT NULL REFERENCES accounts(account_id),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
  feedback_id SERIAL PRIMARY KEY,
  article_ref INTEGER NOT NULL REFERENCES articles(article_id),
  commenter_id INTEGER NOT NULL REFERENCES accounts(account_id),
  reply_to INTEGER REFERENCES feedback(feedback_id),
  message TEXT NOT NULL,
  posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
