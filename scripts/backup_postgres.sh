#!/bin/sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/veya-${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"
umask 077

docker compose -f "${COMPOSE_FILE}" exec -T db sh -c   'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"'   > "${BACKUP_FILE}"

if [ ! -s "${BACKUP_FILE}" ]; then
  echo "Backup file is empty" >&2
  exit 1
fi

sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
echo "${BACKUP_FILE}"
