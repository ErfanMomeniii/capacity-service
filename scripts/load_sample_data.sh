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
    echo "   export DATABASE_URL=postgresql://user:pass@localhost:5432/capacity_db"
    exit 1
fi

# ------------------------------------------------------------
# 3. run_psql function with QUIET mode
# ------------------------------------------------------------
run_psql() {
    local QUIET=${QUIET:-false}

    if command -v psql >/dev/null 2>&1; then
        if [[ "$QUIET" == "true" ]]; then
            psql "$@" 2>/dev/null
        else
            psql "$@"
        fi
    else
        if [[ "$QUIET" != "true" ]]; then
            echo "⚠️  psql not found on host. Trying Docker container..."
        fi

        PG_CONTAINER=$(docker ps --filter "status=running" --format "{{.ID}} {{.Image}}" \
            | grep -i "postgres" | awk '{print $1}' | head -n 1 || true)

        if [[ -z "$PG_CONTAINER" ]]; then
            echo "❌ psql not found and no running Postgres container detected."
            echo "👉 Either install psql locally or ensure your docker-compose Postgres is running."
            exit 1
        fi

        if [[ "$QUIET" != "true" ]]; then
            echo "🐳 Using psql inside Docker container: $PG_CONTAINER"
        fi

        if [[ "$QUIET" == "true" ]]; then
            docker exec -i "$PG_CONTAINER" psql "$@" 2>/dev/null
        else
            docker exec -i "$PG_CONTAINER" psql "$@"
        fi
    fi
}

# ------------------------------------------------------------
# 4. Parse DATABASE_URL
# ------------------------------------------------------------
DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|' || echo "5432")
DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^/?]+).*|\1|')
DB_USER=$(echo "$DATABASE_URL" | sed -E 's|.*://([^:]+):.*|\1|')

# ------------------------------------------------------------
# 5. Ensure database exists (idempotent)
# ------------------------------------------------------------
echo "🔍 Ensuring database '$DB_NAME' exists..."
run_psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/postgres" -v ON_ERROR_STOP=1 -c "
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
# 6. Apply schema if missing
# ------------------------------------------------------------
echo "🚀 Applying schema..."
TABLE_EXISTS=$(QUIET=true run_psql "$DATABASE_URL" -t -A -c "SELECT 1 FROM information_schema.tables WHERE table_name='sailings';" || echo 0)
if [[ -z "$TABLE_EXISTS" ]]; then
    cat migrations/001_create_sailings_table.up.sql | run_psql "$DATABASE_URL"
    echo "✅ Schema applied."
else
    echo "✅ Schema already exists, skipping."
fi

# ------------------------------------------------------------
# 7. Load sample data if table empty
# ------------------------------------------------------------
ROWS_COUNT=$(QUIET=true run_psql "$DATABASE_URL" -t -A -c "SELECT COUNT(*) FROM sailings;" || echo 0)
if [[ "$ROWS_COUNT" -eq 0 ]]; then
    echo "📦 Loading sample data..."
    cat data/sailings_sample.csv | run_psql "$DATABASE_URL" -c "\copy sailings(origin, destination, origin_port_code, destination_port_code, service_version_and_roundtrip_identfiers, origin_service_version_and_master, destination_service_version_and_master, origin_at_utc, offered_capacity_teu) FROM STDIN CSV HEADER"
    echo "✅ Sample data loaded."
else
    echo "✅ Sample data already exists, skipping."
fi

echo "🎉 Database ready."
