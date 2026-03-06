ALTER TABLE accounts
    ALTER COLUMN account_email SET NOT NULL,
    ADD CONSTRAINT accounts_email_unique UNIQUE (account_email);
   