Run from backend: `.venv\Scripts\python.exe -m alembic upgrade head`.
This applies only the configured DATABASE_URL, in one transaction. No import/startup DDL.
The initial revision assumes no Milo tables. It never drops existing data. Stop if a table
already exists and review the schema; do not reset. The migration role must own the tables
and have sufficient privileges to revoke client access (the project's postgres connection).
No functions, views, REST policies, or access grants are added.

For an IPv4 Windows network, copy the exact Session pooler connection from the configured
project's Connect dialog. Do not infer its hostname. Use sslmode=require or stronger.
Percent-encode the database password. A Supabase API secret is neither needed nor used.

Review generated SQL first with `.venv\Scripts\python.exe -m alembic upgrade head --sql`.
If local access is unavailable, generate this SQL after installing dependencies and run it
in that same project's SQL editor; it includes Alembic version tracking. Do not separately
apply SQL and then stamp a different revision.

On 2026-10-03, the reviewed generated SQL was applied to confirmed project
toemuooqjrqfincmzywr through Supabase MCP as 20261003143155_milo_alembic_0001.
Its Alembic version is already 0001_milo. Once DATABASE_URL is configured, alembic current
should report that revision and upgrade head should perform no new DDL.
Do not reapply the initial SQL or stamp a different revision.

Both project advisors were run and all 15 tables' RLS/effective client grants were checked.
Only expected INFO notices remain (deny-by-default RLS without policies, newly unused indexes).
Run check_database.py after the explicit safe seed for application write/read/reconnect.
See ../../VERIFICATION.md for actual results. No unrelated project was inspected.
