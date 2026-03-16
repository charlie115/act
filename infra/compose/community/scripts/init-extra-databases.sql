-- Create additional databases needed by news_core and message_core.
-- PostgreSQL's POSTGRES_DB env var only creates one database at init time.
-- This script runs automatically via docker-entrypoint-initdb.d on first start.

SELECT 'CREATE DATABASE news_core'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'news_core')\gexec

SELECT 'CREATE DATABASE message_core'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'message_core')\gexec
