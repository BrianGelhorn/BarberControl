SELECT 'CREATE DATABASE barberia_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberia_test')\gexec

SELECT 'CREATE DATABASE barberia_prod'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberia_prod')\gexec

\connect barberia_test
\i /docker-entrypoint-initdb.d/schema.sql.txt

\connect barberia_prod
\i /docker-entrypoint-initdb.d/schema.sql.txt
