#!/bin/sh
set -e

# Cloud Run native entrypoint
# Note: Migrations are handled outside of the container lifecycle via Cloud SQL Auth Proxy/Cloud Build.
# Cloud SQL connectivity is guaranteed by the Cloud Run runtime via Unix sockets.

# GeoIP setup
mkdir -p ./data
python scripts/download_geoip.py

# Start server
echo "Starting gunicorn for production..."
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 1 --threads 8 --timeout 0 --bind 0.0.0.0:${PORT:-8000}
