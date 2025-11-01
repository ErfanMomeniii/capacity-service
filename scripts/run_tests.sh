#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${TEST_DATABASE_URL:-}" ]]; then
  echo "Please set TEST_DATABASE_URL environment variable, e.g.:"
  echo "  export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres"
  exit 1
fi

pytest -q