#!/bin/bash
# LexIntellectus - Automated Encrypted DB Backup Script
set -e

# Load environment variables if needed or assume environment holds them
DB_HOST=${POSTGRES_HOST:-"postgres"}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-"lexintellectus"}
DB_PASS=${POSTGRES_PASSWORD:-"lexintellectus_dev_2026"}
DB_NAME=${POSTGRES_DB:-"lexintellectus"}
ENCRYPTION_KEY=${DB_ENCRYPTION_KEY:-"T1Boc2QzSDRlNTZkNzhqOWowMTIzNDU2NzhqOWowMTI="}
MINIO_ENDPOINT=${MINIO_ENDPOINT:-"minio:9000"}
MINIO_USER=${MINIO_ROOT_USER:-"lexintellectus"}
MINIO_PASSWORD=${MINIO_ROOT_PASSWORD:-"lexintellectus_minio_2026"}
MINIO_BUCKET="lexintellectus-backups"

BACKUP_DIR="/tmp/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PLAIN_BACKUP="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
ENCRYPTED_BACKUP="${PLAIN_BACKUP}.enc"

echo "Starting database backup for $DB_NAME..."

# Execute pg_dump
PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F p > "$PLAIN_BACKUP"

echo "Encrypting backup file with AES-256..."
# Encrypt using openssl with PBKDF2 (extremely secure symmetric encryption)
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 10000 -pass "pass:$ENCRYPTION_KEY" -in "$PLAIN_BACKUP" -out "$ENCRYPTED_BACKUP"

echo "Uploading encrypted backup to MinIO bucket '$MINIO_BUCKET'..."
# Use Python with MinIO library to upload, which is 100% reliable inside the python containers!
python3 -c "
import os
from minio import Minio

endpoint = '${MINIO_ENDPOINT}'
user = '${MINIO_USER}'
password = '${MINIO_PASSWORD}'
bucket = '${MINIO_BUCKET}'
file_path = '${ENCRYPTED_BACKUP}'
object_name = 'db_backups/' + os.path.basename(file_path)

client = Minio(endpoint, access_key=user, secret_key=password, secure=False)
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)
client.fput_object(bucket, object_name, file_path)
print('Successfully uploaded ' + object_name + ' to MinIO!')
"

# Clean up
rm -f "$PLAIN_BACKUP" "$ENCRYPTED_BACKUP"
echo "Backup and upload completed successfully!"
