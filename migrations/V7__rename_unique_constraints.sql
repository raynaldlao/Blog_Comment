ALTER TABLE accounts
    RENAME CONSTRAINT accounts_username_key TO accounts_account_username_key;

ALTER TABLE accounts
    RENAME CONSTRAINT accounts_email_unique TO accounts_account_email_key;
