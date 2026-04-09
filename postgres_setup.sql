-- Run in pgAdmin Query Tool or psql as superuser (e.g. postgres).
-- Keep the password identical to DB_PASSWORD in .env.

-- A) If user & DB already exist but Django says "password authentication failed":
ALTER USER billing_user WITH PASSWORD 'your_strong_password';

-- B) First-time only — uncomment if billing_user / billing_db are missing:
-- CREATE USER billing_user WITH PASSWORD 'your_strong_password';
-- CREATE DATABASE billing_db OWNER billing_user;
-- GRANT ALL PRIVILEGES ON DATABASE billing_db TO billing_user;
