#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.dump>" >&2
  exit 2
fi

if [ "${ALLOW_DATABASE_RESTORE:-}" != "yes" ]; then
  echo "Refusing restore. Set ALLOW_DATABASE_RESTORE=yes after entering maintenance mode." >&2
  exit 1
fi

BACKUP_FILE="$1"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"

test -f "${BACKUP_FILE}"

if [ -f "${CHECKSUM_FILE}" ]; then
  sha256sum -c "${CHECKSUM_FILE}"
fi

echo "Restoring PostgreSQL database from ${BACKUP_FILE}..." >&2
cat "${BACKUP_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T db sh -c   'pg_restore --clean --if-exists --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB" -'

echo "Restore complete. Run application smoke tests before leaving maintenance mode." >&2
