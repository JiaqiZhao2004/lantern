-- Run through psql as the bootstrap/admin Postgres role.
-- Pass app_password as a psql variable, without committing the value:
--
--   psql -v app_password='replace-me' -f create-app-role.sql

SELECT format('CREATE ROLE lantern_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lantern_app')
\gexec

SELECT format('ALTER ROLE lantern_app LOGIN PASSWORD %L', :'app_password')
\gexec

GRANT CONNECT, TEMPORARY ON DATABASE lantern TO lantern_app;
GRANT USAGE, CREATE ON SCHEMA public TO lantern_app;
