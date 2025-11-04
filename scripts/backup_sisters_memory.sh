#!/bin/bash
# sisters_memory.db Backup Script
#
# Purpose: Physical protection against hardware failure, filesystem corruption, accidental deletion
# Prohibition: NEVER use for logical rollback (undo discussion results, memory changes)

set -euo pipefail

# Configuration
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SOURCE_DB="/home/koshikawa/toExecUnit/sisters_memory.db"
LOCAL_BACKUP_DIR="/home/koshikawa/toExecUnit/backup"
REMOTE_HOST="sakura-vps"
REMOTE_DIR="/home/ubuntu/sisters_backup"
LOG_FILE="/home/koshikawa/toExecUnit/logs/backup_sisters_memory.log"

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=5  # seconds

# Backup filename
BACKUP_FILENAME="sisters_memory_${TIMESTAMP}.db"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Backup Start ==="

# Check if source DB exists
if [ ! -f "$SOURCE_DB" ]; then
    log "ERROR: Source DB not found: $SOURCE_DB"
    exit 1
fi

# Create local backup directory if not exists
mkdir -p "$LOCAL_BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Local backup
log "Creating local backup..."
cp "$SOURCE_DB" "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
if [ $? -eq 0 ]; then
    log "SUCCESS: Local backup created: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
else
    log "ERROR: Local backup failed"
    exit 1
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
    log "ERROR: Remote backup failed after $MAX_RETRIES attempts"

    # Delete failed local backup file to prevent orphan files
    log "Cleaning up failed local backup: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
    rm -f "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
    log "Failed backup file removed"

    # Send email alert via VPS (try with retry)
    ALERT_SUBJECT="[ERROR] Sisters Memory Backup Failed"
    ALERT_BODY="Remote backup upload FAILED after $MAX_RETRIES attempts at $(date '+%Y-%m-%d %H:%M:%S')

Source: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME (DELETED to prevent orphan files)
Destination: $REMOTE_HOST:$REMOTE_DIR/$BACKUP_FILENAME

Local backup has been REMOVED to maintain consistency.
Previous backups are still available.

Please investigate VPS connection and storage immediately.

---
Automated alert from Sisters Memory Backup System"

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

    exit 1
fi

# Archive old local backups before cleanup (keep last 10)
log "Archiving old local backups..."
ARCHIVE_DIR="$LOCAL_BACKUP_DIR/archive"
mkdir -p "$ARCHIVE_DIR"
cd "$LOCAL_BACKUP_DIR"

OLD_LOCAL_FILES=$(ls -t sisters_memory_*.db 2>/dev/null | tail -n +11)
if [ -n "$OLD_LOCAL_FILES" ]; then
    ARCHIVE_NAME="sisters_memory_archive_${TIMESTAMP}.tar.gz"
    echo "$OLD_LOCAL_FILES" | xargs tar -czf "$ARCHIVE_DIR/$ARCHIVE_NAME"
    if [ $? -eq 0 ]; then
        log "SUCCESS: Archived old local backups to $ARCHIVE_DIR/$ARCHIVE_NAME"
        # Now safe to delete
        echo "$OLD_LOCAL_FILES" | xargs rm
        log "Deleted archived local backups"
    else
        log "ERROR: Failed to archive local backups, keeping original files"
    fi
else
    log "No old local backups to archive"
fi

LOCAL_COUNT=$(ls -1 sisters_memory_*.db 2>/dev/null | wc -l)
log "Local backups kept: $LOCAL_COUNT"

# Archive old remote backups before cleanup (keep last 10)
log "Archiving old remote backups on VPS..."
ssh "$REMOTE_HOST" bash <<EOF >> "$LOG_FILE" 2>&1
    set -e
    cd $REMOTE_DIR
    mkdir -p archive

    OLD_FILES=\$(ls -t sisters_memory_*.db 2>/dev/null | tail -n +11)
    if [ -n "\$OLD_FILES" ]; then
        ARCHIVE_NAME="sisters_memory_archive_${TIMESTAMP}.tar.gz"
        echo "\$OLD_FILES" | xargs tar -czf archive/\$ARCHIVE_NAME
        if [ \$? -eq 0 ]; then
            echo "[INFO] Archived old remote backups to archive/\$ARCHIVE_NAME"
            # Now safe to delete
            echo "\$OLD_FILES" | xargs rm
            echo "[INFO] Deleted archived remote backups"
        else
            echo "[ERROR] Failed to archive remote backups, keeping original files"
        fi
    else
        echo "[INFO] No old remote backups to archive"
    fi
EOF

if [ $? -eq 0 ]; then
    REMOTE_COUNT=$(ssh "$REMOTE_HOST" "ls -1 $REMOTE_DIR/sisters_memory_*.db 2>/dev/null | wc -l")
    log "Remote backups kept: $REMOTE_COUNT"
else
    log "WARNING: Remote archiving failed"
fi

log "=== Backup Complete ==="

# Run integrity check
log "Running integrity check..."
/home/koshikawa/toExecUnit/scripts/check_backup_integrity.sh
if [ $? -eq 0 ]; then
    log "Integrity check: OK"
else
    log "Integrity check: ALERTS DETECTED"
fi

log ""
