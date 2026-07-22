# Testing

## Database

Postgres and Cockroach are started automatically via testcontainers, so
Docker needs to be running.

To use an external database instead, set `TESTCONTAINERS=false` and point
`PG_HOST` / `PG_PORT` / `PG_DATABASE` / `PG_USER` / `PG_PASSWORD` at it (see
`postgres_conf.py`).
