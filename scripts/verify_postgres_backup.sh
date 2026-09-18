#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.dump>" >&2
  exit 2
fi

BACKUP_FILE="$1"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"

test -f "${BACKUP_FILE}"

if [ -f "${CHECKSUM_FILE}" ]; then
  sha256sum -c "${CHECKSUM_FILE}"
fi

cat "${BACKUP_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T db   pg_restore --list >/dev/null

echo "Backup verified: ${BACKUP_FILE}"
