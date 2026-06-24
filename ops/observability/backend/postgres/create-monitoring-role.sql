-- Run through psql as a database superuser or owner role.
-- Pass monitor_password as a psql variable, without committing the value:
--
--   psql -v monitor_password='replace-me' -f create-monitoring-role.sql

SELECT format('CREATE ROLE lantern_monitor LOGIN PASSWORD %L', :'monitor_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lantern_monitor')
\gexec

SELECT format('ALTER ROLE lantern_monitor LOGIN PASSWORD %L', :'monitor_password')
\gexec

GRANT pg_monitor TO lantern_monitor;
