#!/bin/bash
# Railway "worker" service start command. Runs Celery worker + beat in one
# process (-B) — acceptable at single-pharmacy scale; split into separate
# services when beat schedule reliability matters more than cost.
set -e

if [[ "${APP_ENV,,}" == "production" || "${APP_ENV,,}" == "prod" ]] && [[ -z "${DEBUG}" ]]; then
    export DEBUG=false
fi

exec celery -A app.celery_app worker -B --loglevel=info --concurrency=2
