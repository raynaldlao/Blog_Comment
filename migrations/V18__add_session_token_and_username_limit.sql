ALTER TABLE accounts
  ADD COLUMN session_token VARCHAR(64);

ALTER TABLE accounts
  ALTER COLUMN account_username TYPE VARCHAR(30);
