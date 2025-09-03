#!/bin/bash
set -euo pipefail

CONTAINER="${CONTAINER:-docker_lab-db-1}"
DB_USER="${DB_USER:-user}"
DB_NAME="${DB_NAME:-testdb}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_COUNT="${KEEP_COUNT:-7}"

TIMESTAMP="$(date +%F_%H-%M-%S)"
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"
TMP_FILE="${BACKUP_FILE}.tmp"


if ! command -v docker >/dev/null 2>&1; then
	echo "ERROR: docker CLI not found in PATH" >&2
	exit 2
fi

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
	echo "ERROR: container '$CONTAINER' not running or not found." >&2
	echo "Running containers:" >&2
	docker ps --format '	{{.Names}}' >&2 || true
	exit 3
fi


mkdir -p "$BACKUP_DIR"

trap 'rm -f "$TMP_FILE" >/dev/null 2>&1 || true' EXIT

echo "Starting backup: container='$CONTAINER', db='$DB_NAME', user='$DB_USER'"

if docker exec -i "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$TMP_FILE"; then
	mv "$TMP_FILE" "$BACKUP_FILE"
	echo "Backup created: $BACKUP_FILE"
else
	echo "Backup failed!" >&2
	exit 4
fi


if [ "${KEEP_COUNT:-0}" -gt 0 ]; then
	echo "Pruning backups, keeping latest $KEEP_COUNT..."
	files_count=$(ls -1t "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | wc -l || true)
	if [ "$files_count" -gt "$KEEP_COUNT" ]; then
		ls -1t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +"$((KEEP_COUNT+1))" | xargs -r rm -f --
		echo "Old backups removed."
	else
		echo "No old backups to remove (found $files_count files)."
	fi
fi

echo "Backup script finished successfully."

