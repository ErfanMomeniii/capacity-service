#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# 1. Load environment variables
# ------------------------------------------------------------
if [[ -f ".env" ]]; then
    echo "🧩 Loading environment from .env file"
    set -a
    source .env
    set +a
else
    echo "⚠️ No .env file found, relying on existing environment variables"
fi

# ------------------------------------------------------------
# 2. Ensure DATABASE_URL is set
# ------------------------------------------------------------
if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "❌ DATABASE_URL must be set, e.g.:"
    echo "   export DATABASE_URL=postgresql://user:pass@db:5432/capacity_db"
    exit 1
fi

# ------------------------------------------------------------
# 3. Parse DATABASE_URL
# ------------------------------------------------------------
DB_USER=$(echo "$DATABASE_URL" | sed -E 's|.*://([^:]+):.*|\1|')
DB_PASSWORD=$(echo "$DATABASE_URL" | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|' || echo "5432")
DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^/?]+).*|\1|')

export PGPASSWORD="$DB_PASSWORD"

# ------------------------------------------------------------
# 4. Wait for Postgres to be ready
# ------------------------------------------------------------
echo "⏳ Waiting for Postgres at $DB_HOST:$DB_PORT ..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    sleep 1
done
echo "✅ Postgres ready!"

# ------------------------------------------------------------
# 5. Helper function to run psql
# ------------------------------------------------------------
run_psql() {
    psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$1" "${@:2}"
}

# ------------------------------------------------------------
# 6. Ensure database exists (idempotent)
# ------------------------------------------------------------
echo "🔍 Ensuring database '$DB_NAME' exists..."
run_psql "postgres" -v ON_ERROR_STOP=1 -c "
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
      CREATE DATABASE $DB_NAME;
      RAISE NOTICE 'Database $DB_NAME created.';
   ELSE
      RAISE NOTICE 'Database $DB_NAME already exists.';
   END IF;
END
\$\$;
"

# ------------------------------------------------------------
# 7. Apply schema if missing
# ------------------------------------------------------------
echo "🚀 Applying schema..."
TABLE_EXISTS=$(run_psql "$DB_NAME" -t -A -c "SELECT 1 FROM information_schema.tables WHERE table_name='sailings';" || echo 0)
if [[ -z "$TABLE_EXISTS" ]]; then
    cat migrations/001_create_sailings_table.up.sql | run_psql "$DB_NAME"
    echo "✅ Schema applied."
else
    echo "✅ Schema already exists, skipping."
fi

# ------------------------------------------------------------
# 8. Load sample data if table empty
# ------------------------------------------------------------
ROWS_COUNT=$(run_psql "$DB_NAME" -t -A -c "SELECT COUNT(*) FROM sailings;" || echo 0)
if [[ "$ROWS_COUNT" -eq 0 ]]; then
    echo "📦 Loading sample data..."
    cat data/sailings_sample.csv | run_psql "$DB_NAME" -c "\copy sailings(origin, destination, origin_port_code, destination_port_code, service_version_and_roundtrip_identfiers, origin_service_version_and_master, destination_service_version_and_master, origin_at_utc, offered_capacity_teu) FROM STDIN CSV HEADER"
    echo "✅ Sample data loaded."
else
    echo "✅ Sample data already exists, skipping."
fi

echo "🎉 Database ready."
