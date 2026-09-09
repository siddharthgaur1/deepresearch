#!/bin/sh
# Runs the Celery worker in the background and the API in the foreground.
# Only used for the free-tier "combo" deploy (see docs/DEPLOY_FREE.md) where
# there's no separate worker dyno. If the worker process dies, this script
# doesn't restart it — a stuck job is the visible symptom (see README's
# "degrade visibly" philosophy); check Render logs for the celery traceback.
set -e

# Render's dedicated migration hook (preDeployCommand) is behind a paid plan, so
# migrations run here, before anything serves traffic. `%(here)s` in alembic.ini
# resolves script_location relative to the ini, so -c is enough from /app.
alembic -c backend/alembic.ini upgrade head

celery -A backend.workers.celery_app worker --loglevel=info --concurrency=2 &

exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
