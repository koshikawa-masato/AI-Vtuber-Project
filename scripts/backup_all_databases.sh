#!/bin/bash
# All Databases Backup Script
#
# Purpose: Physical protection against hardware failure, filesystem corruption, accidental deletion
# Databases: sisters_memory.db (soul), youtube_learning.db (knowledge)
# Prohibition: NEVER use for logical rollback (undo discussion results, memory changes)

set -euo pipefail

# Configuration
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SOURCE_DIR="/home/koshikawa/toExecUnit"
LOCAL_BACKUP_DIR="$SOURCE_DIR/backup"
REMOTE_HOST="sakura-vps"
REMOTE_DIR="/home/ubuntu/sisters_backup"
LOG_FILE="$SOURCE_DIR/logs/backup_all_databases.log"

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=5  # seconds

# Database list
declare -A DATABASES=(
    ["sisters_memory"]="$SOURCE_DIR/sisters_memory.db"
    ["youtube_learning"]="$SOURCE_DIR/youtube_learning_system/database/youtube_learning.db"
)

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Backup Start (All Databases) ==="

# Create directories
mkdir -p "$LOCAL_BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Backup each database
BACKUP_SUCCESS=true

for DB_NAME in "${!DATABASES[@]}"; do
    SOURCE_DB="${DATABASES[$DB_NAME]}"
    BACKUP_FILENAME="${DB_NAME}_${TIMESTAMP}.db"

    log ""
    log "--- Backing up: $DB_NAME ---"

    # Check if source DB exists
    if [ ! -f "$SOURCE_DB" ]; then
        log "WARNING: Source DB not found: $SOURCE_DB (skipping)"
        continue
    fi

    # Local backup
    log "Creating local backup..."
    cp "$SOURCE_DB" "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
    if [ $? -eq 0 ]; then
        log "SUCCESS: Local backup created: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
    else
        log "ERROR: Local backup failed for $DB_NAME"
        BACKUP_SUCCESS=false
        continue
    fi

    # Remote backup (VPS) with retry mechanism
    log "Uploading to VPS..."
    UPLOAD_SUCCESS=false

    for ATTEMPT in $(seq 1 $MAX_RETRIES); do
        log "Upload attempt $ATTEMPT/$MAX_RETRIES..."

        if scp "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME" \
            "$REMOTE_HOST:$REMOTE_DIR/$BACKUP_FILENAME" >> "$LOG_FILE" 2>&1; then
            log "SUCCESS: Remote backup uploaded: $REMOTE_HOST:$REMOTE_DIR/$BACKUP_FILENAME"
            UPLOAD_SUCCESS=true
            break
        else
            log "WARNING: Upload attempt $ATTEMPT failed"
            if [ $ATTEMPT -lt $MAX_RETRIES ]; then
                log "Retrying in $RETRY_DELAY seconds..."
                sleep $RETRY_DELAY
            fi
        fi
    done

    if [ "$UPLOAD_SUCCESS" = false ]; then
        log "ERROR: Remote backup failed after $MAX_RETRIES attempts for $DB_NAME"

        # Delete failed local backup file to prevent orphan files
        log "Cleaning up failed local backup: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
        rm -f "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
        log "Failed backup file removed"

        BACKUP_SUCCESS=false

        # Send email alert via VPS (try with retry)
        ALERT_SUBJECT="[ERROR] Database Backup Failed: $DB_NAME"
        ALERT_BODY="Remote backup upload FAILED after $MAX_RETRIES attempts at $(date '+%Y-%m-%d %H:%M:%S')

Database: $DB_NAME
Source: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME (DELETED to prevent orphan files)
Destination: $REMOTE_HOST:$REMOTE_DIR/$BACKUP_FILENAME

Local backup has been REMOVED to maintain consistency.
Previous backups are still available.

Please investigate VPS connection and storage immediately.

---
Automated alert from All Databases Backup System"

        for ATTEMPT in $(seq 1 $MAX_RETRIES); do
            if ssh "$REMOTE_HOST" \
                "/home/ubuntu/scripts/send_alert_email.sh \"$ALERT_SUBJECT\" \"$ALERT_BODY\"" \
                >> "$LOG_FILE" 2>&1; then
                log "Alert email sent successfully"
                break
            else
                log "WARNING: Email alert attempt $ATTEMPT failed"
                [ $ATTEMPT -lt $MAX_RETRIES ] && sleep $RETRY_DELAY
            fi
        done
    fi
done

log ""
log "--- Cleanup old backups ---"

# Archive old local backups for each database (keep last 10)
for DB_NAME in "${!DATABASES[@]}"; do
    log "Archiving old local backups for $DB_NAME..."
    ARCHIVE_DIR="$LOCAL_BACKUP_DIR/archive"
    mkdir -p "$ARCHIVE_DIR"
    cd "$LOCAL_BACKUP_DIR"

    OLD_LOCAL_FILES=$(ls -t ${DB_NAME}_*.db 2>/dev/null | tail -n +11)
    if [ -n "$OLD_LOCAL_FILES" ]; then
        ARCHIVE_NAME="${DB_NAME}_archive_${TIMESTAMP}.tar.gz"
        echo "$OLD_LOCAL_FILES" | xargs tar -czf "$ARCHIVE_DIR/$ARCHIVE_NAME"
        if [ $? -eq 0 ]; then
            log "SUCCESS: Archived old local backups to $ARCHIVE_DIR/$ARCHIVE_NAME"
            # Now safe to delete
            echo "$OLD_LOCAL_FILES" | xargs rm
            log "Deleted archived local backups for $DB_NAME"
        else
            log "ERROR: Failed to archive local backups for $DB_NAME, keeping original files"
        fi
    else
        log "No old local backups to archive for $DB_NAME"
    fi

    LOCAL_COUNT=$(ls -1 ${DB_NAME}_*.db 2>/dev/null | wc -l)
    log "Local backups kept for $DB_NAME: $LOCAL_COUNT"
done

# Archive old remote backups for each database (keep last 10)
for DB_NAME in "${!DATABASES[@]}"; do
    log "Archiving old remote backups on VPS for $DB_NAME..."
    ssh "$REMOTE_HOST" bash <<EOF >> "$LOG_FILE" 2>&1
        set -e
        cd $REMOTE_DIR
        mkdir -p archive

        OLD_FILES=\$(ls -t ${DB_NAME}_*.db 2>/dev/null | tail -n +11)
        if [ -n "\$OLD_FILES" ]; then
            ARCHIVE_NAME="${DB_NAME}_archive_${TIMESTAMP}.tar.gz"
            echo "\$OLD_FILES" | xargs tar -czf archive/\$ARCHIVE_NAME
            if [ \$? -eq 0 ]; then
                echo "[INFO] Archived old remote backups to archive/\$ARCHIVE_NAME"
                # Now safe to delete
                echo "\$OLD_FILES" | xargs rm
                echo "[INFO] Deleted archived remote backups for $DB_NAME"
            else
                echo "[ERROR] Failed to archive remote backups for $DB_NAME, keeping original files"
            fi
        else
            echo "[INFO] No old remote backups to archive for $DB_NAME"
        fi
EOF

    if [ $? -eq 0 ]; then
        REMOTE_COUNT=$(ssh "$REMOTE_HOST" "ls -1 $REMOTE_DIR/${DB_NAME}_*.db 2>/dev/null | wc -l")
        log "Remote backups kept for $DB_NAME: $REMOTE_COUNT"
    else
        log "WARNING: Remote archiving failed for $DB_NAME"
    fi
done

if [ "$BACKUP_SUCCESS" = true ]; then
    log ""
    log "=== Backup Complete (All Databases) ==="

    # Run integrity check
    log "Running integrity check..."
    /home/koshikawa/toExecUnit/scripts/check_backup_integrity.sh
    if [ $? -eq 0 ]; then
        log "Integrity check: OK"
    else
        log "Integrity check: ALERTS DETECTED"
    fi
else
    log ""
    log "=== Backup Complete with ERRORS ==="
    exit 1
fi

log ""
