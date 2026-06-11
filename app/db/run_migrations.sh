#!/bin/sh
set -eu

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-mlflow}"
POSTGRES_DB="${POSTGRES_DB:-memoraweave_db}"
MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"

export PGPASSWORD="${POSTGRES_PASSWORD:-mlflow123}"

echo "Waiting for PostgreSQL..."

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  sleep 1
done

echo "PostgreSQL is ready."

psql \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 <<'SQL'
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.schema_migrations (
    filename text PRIMARY KEY,
    checksum text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);
SQL

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

for file in "$MIGRATIONS_DIR"/*.sql; do
  [ -e "$file" ] || continue

  filename="$(basename "$file")"
  filename_sql="$(sql_escape "$filename")"
  checksum="$(sha256sum "$file" | awk '{print $1}')"
  checksum_sql="$(sql_escape "$checksum")"

  already_applied="$(
    psql \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -tAc "SELECT EXISTS (SELECT 1 FROM app.schema_migrations WHERE filename = '$filename_sql');"
  )"

  if [ "$already_applied" = "t" ]; then
    echo "Skipping $filename, already applied."
  else
    echo "Applying $filename..."

    psql \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -v ON_ERROR_STOP=1 \
      -f "$file"

    psql \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -v ON_ERROR_STOP=1 \
      -c "INSERT INTO app.schema_migrations (filename, checksum) VALUES ('$filename_sql', '$checksum_sql');"

    echo "Applied $filename."
  fi
done

echo "Migrations completed."
