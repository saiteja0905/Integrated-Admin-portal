#!/bin/sh
# Prepare the uploads directory, then run the server as the unprivileged app user.
#
# UPLOAD_DIR points at a mounted volume in production (a Fly volume, or a Docker
# volume in docker-compose). Fresh volumes are mounted owned by root, so the
# directory has to be created and handed over before dropping privileges -
# otherwise uploads fail with "permission denied" on the first deploy.
set -e

UPLOAD_DIR="${UPLOAD_DIR:-/app/uploads}"
mkdir -p "$UPLOAD_DIR"
chown -R app:app "$UPLOAD_DIR"

exec gosu app "$@"
