#!/usr/bin/env bash
set -e

echo "⏳ Waiting for database..."
until nc -z db 5432; do sleep 1; done
echo "✅ DB ready!"

echo "🚀 Running migrations..."
psql "$DATABASE_URL" -f migrations/001_create_sailings_table.up.sql

echo "🎉 Migration complete!"
