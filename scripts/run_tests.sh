#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${TEST_DATABASE_URL:-}" ]]; then
    echo "Please set TEST_DATABASE_URL environment variable"
    exit 1
fi

pytest --cov=app --cov-report=term-missing --cov-report=html:coverage_report -v tests/