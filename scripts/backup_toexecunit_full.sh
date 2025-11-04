#!/bin/bash
# toExecUnit Full Backup Script
#
# Purpose: Complete backup of toExecUnit directory to VPS
# Frequency: Weekly (recommended)
# Excludes: venv, .git, backup/, logs/, *.db, large TTS projects

set -euo pipefail

# Configuration
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SOURCE_DIR="/home/koshikawa/toExecUnit"
LOCAL_BACKUP_DIR="/tmp"
REMOTE_HOST="sakura-vps"
REMOTE_DIR="/home/ubuntu/sisters_backup/toexecunit_full"
LOG_FILE="$SOURCE_DIR/logs/backup_toexecunit_full.log"

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=5  # seconds

# Backup filename
BACKUP_FILENAME="toExecUnit_full_${TIMESTAMP}.tar.gz"
LOCAL_BACKUP_PATH="${LOCAL_BACKUP_DIR}/${BACKUP_FILENAME}"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== toExecUnit Full Backup Start ==="

# Create directories
mkdir -p "$(dirname "$LOG_FILE")"

# Create backup with comprehensive exclusions
log "Creating tar.gz archive..."
log "Excluding: venv, .git, backup/, logs/, *.db, large TTS projects"

cd /home/koshikawa

tar -czf "$LOCAL_BACKUP_PATH" \
  --exclude='toExecUnit/.git' \
  --exclude='toExecUnit/backup' \
  --exclude='toExecUnit/logs' \
  --exclude='toExecUnit/venv' \
  --exclude='toExecUnit/*/venv' \
  --exclude='toExecUnit/__pycache__' \
  --exclude='toExecUnit/*/__pycache__' \
  --exclude='toExecUnit/*.db' \
  --exclude='toExecUnit/youtube_learning_system' \
  --exclude='toExecUnit/GPT-SoVITS' \
  --exclude='toExecUnit/Style-Bert-VITS2' \
  --exclude='toExecUnit/Style-Bert-VITS2-v2' \
  --exclude='toExecUnit/fish-speech' \
  --exclude='toExecUnit/tts_manager' \
  --exclude='toExecUnit/voice_free' \
  --exclude='toExecUnit/venv_webui' \
  toExecUnit

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(ls -lh "$LOCAL_BACKUP_PATH" | awk '{print $5}')
    log "SUCCESS: Local backup created: $LOCAL_BACKUP_PATH ($BACKUP_SIZE)"
else
    log "ERROR: Local backup failed"
    exit 1
fi

# Ensure remote directory exists
log "Ensuring remote directory exists..."
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR" >> "$LOG_FILE" 2>&1

# Remote backup (VPS) with retry mechanism
log "Uploading to VPS..."
UPLOAD_SUCCESS=false

for ATTEMPT in $(seq 1 $MAX_RETRIES); do
    log "Upload attempt $ATTEMPT/$MAX_RETRIES..."

    if scp "$LOCAL_BACKUP_PATH" \
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

    # Delete local backup to prevent orphan files
    log "Cleaning up failed local backup: $LOCAL_BACKUP_PATH"
    rm -f "$LOCAL_BACKUP_PATH"
    log "Failed backup file removed"

    # Send email alert via VPS (try with retry)
    ALERT_SUBJECT="[ERROR] toExecUnit Full Backup Failed"
    ALERT_BODY="Remote backup upload FAILED after $MAX_RETRIES attempts at $(date '+%Y-%m-%d %H:%M:%S')

Source: $LOCAL_BACKUP_PATH (DELETED to prevent orphan files)
Destination: $REMOTE_HOST:$REMOTE_DIR/$BACKUP_FILENAME

Local backup has been REMOVED to maintain consistency.
Previous backups are still available.

Please investigate VPS connection and storage immediately.

---
Automated alert from toExecUnit Full Backup System"

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

# Delete local backup after successful upload
log "Cleaning up local backup file..."
rm -f "$LOCAL_BACKUP_PATH"
log "Local backup file removed from /tmp"

log ""
log "--- Cleanup old backups ---"

# Archive old remote backups (keep last 10)
log "Archiving old remote backups on VPS..."
ssh "$REMOTE_HOST" bash <<EOF >> "$LOG_FILE" 2>&1
    set -e
    cd $REMOTE_DIR
    mkdir -p archive

    OLD_FILES=\$(ls -t toExecUnit_full_*.tar.gz 2>/dev/null | tail -n +11)
    if [ -n "\$OLD_FILES" ]; then
        ARCHIVE_NAME="toExecUnit_full_archive_${TIMESTAMP}.tar.gz"
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
    REMOTE_COUNT=$(ssh "$REMOTE_HOST" "ls -1 $REMOTE_DIR/toExecUnit_full_*.tar.gz 2>/dev/null | wc -l")
    log "Remote backups kept: $REMOTE_COUNT"
else
    log "WARNING: Remote archiving failed"
fi

log ""
log "=== toExecUnit Full Backup Complete ==="
log ""
