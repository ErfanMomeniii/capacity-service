#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "❌ DATABASE_URL env variable must be set, e.g.:"
  echo "   export DATABASE_URL=postgresql://user:pass@localhost:5432/capacity_db"
  exit 1
fi

echo "🚀 Loading schema..."
psql "$DATABASE_URL" -f db/schema.sql

echo "📦 Loading sample data..."
psql "$DATABASE_URL" -c "\copy sailings(service_version_and_roundtrip_identfiers, origin_service_version_and_master, destination_service_version_and_master, vessel_identifier, origin_port_code, destination_port_code, origin_at_utc, offered_capacity_teu) FROM 'data/sailings_sample.csv' CSV HEADER"

echo "✅ Done."
