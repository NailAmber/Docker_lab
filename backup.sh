#!/bin/bash
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_DIR=./backups/
BACKUP_FILE=$BACKUP_DIR/backup_$TIMESTAMP.sql

mkdir -p $BACKUP_DIR

if docker exec mydb pg_dump -U user testdb > ./backups/backup_$TIMESTAMP.sql; then
	echo "Backup created: backups/backup_$TIMESTAMP.sql"
else
	echo "Backup failed!"
	rm -f $BACKUP_FILE
fi
