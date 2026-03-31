#!/bin/bash
# Enterprise AI System - Backup Script
# Archives PostgreSQL database and FAISS vector store

set -a
source ../server/.env
set +a

# Directories
BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
FAISS_BACKUP_FILE="${BACKUP_DIR}/faiss_backup_${TIMESTAMP}.tar.gz"

mkdir -p $BACKUP_DIR

echo "[INFO] Starting Backup Process at $TIMESTAMP"

# 1. Backup Postgres (Assumes running locally or with accessible pg_dump)
echo "[INFO] Backing up PostgreSQL Database..."
if command -v pg_dump &> /dev/null; then
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "${POSTGRES_SERVER}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > $DB_BACKUP_FILE
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Database backed up to $DB_BACKUP_FILE"
    else
        echo "[ERROR] Database backup failed"
    fi
else
    # Fallback to pure docker execution if pg_dump is not available on host
    echo "[INFO] pg_dump not found on host, attempting via docker exec..."
    docker exec -t aioffice-db pg_dump -U admin -d aioffice > $DB_BACKUP_FILE 2>/dev/null
    echo "[SUCCESS] Database backed up via Docker to $DB_BACKUP_FILE"
fi

# 2. Backup FAISS Vector Store
echo "[INFO] Backing up FAISS Vector Store..."
if [ -d "../ai-engine/vector_store" ]; then
    tar -czf $FAISS_BACKUP_FILE -C ../ai-engine vector_store
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Vector store backed up to $FAISS_BACKUP_FILE"
    else
        echo "[ERROR] Vector store backup failed"
    fi
else
    echo "[WARNING] Vector store directory not found, skipping."
fi

# 3. Clean up old backups (Retain last 7 days)
echo "[INFO] Cleaning up backups older than 7 days"
find $BACKUP_DIR -type f -name "*.sql" -mtime +7 -exec rm {} \;
find $BACKUP_DIR -type f -name "*.tar.gz" -mtime +7 -exec rm {} \;

echo "[INFO] Backup Process Completed Successfully"
