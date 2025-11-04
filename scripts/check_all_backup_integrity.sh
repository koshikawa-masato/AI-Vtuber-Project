#!/bin/bash
# All Databases Backup Integrity Check Script
#
# Purpose: Verify local and remote backups are in perfect sync for all databases
# Databases: sisters_memory (soul), youtube_learning (knowledge)
# Usage: Called by Claude Code on startup, and after each backup

set -euo pipefail

# Configuration
LOCAL_BACKUP_DIR="/home/koshikawa/toExecUnit/backup"
REMOTE_HOST="sakura-vps"
REMOTE_DIR="/home/ubuntu/sisters_backup"
LOG_FILE="/home/koshikawa/toExecUnit/logs/backup_integrity.log"
ALERT_FILE="/home/koshikawa/toExecUnit/logs/backup_alert.txt"

# Database prefixes
DB_PREFIXES=("sisters_memory" "youtube_learning")

# Create log directory if not exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Clear previous alert
rm -f "$ALERT_FILE"

log "=== Backup Integrity Check Start (All Databases) ==="

OVERALL_STATUS="OK"

for DB_PREFIX in "${DB_PREFIXES[@]}"; do
    log ""
    log "--- Checking: $DB_PREFIX ---"

    # 1. Get local backup list
    log "Checking local backups..."
    if [ ! -d "$LOCAL_BACKUP_DIR" ]; then
        echo "CRITICAL: Local backup directory not found" >> "$ALERT_FILE"
        log "ERROR: Local backup directory not found: $LOCAL_BACKUP_DIR"
        OVERALL_STATUS="ERROR"
        continue
    fi

    LOCAL_FILES=$(cd "$LOCAL_BACKUP_DIR" && ls -1 ${DB_PREFIX}_*.db 2>/dev/null | sort || true)
    LOCAL_COUNT=$(echo "$LOCAL_FILES" | grep -c . || echo 0)
    log "Local backups found: $LOCAL_COUNT"

    # 2. Get remote backup list
    log "Checking remote backups..."
    REMOTE_FILES=$(ssh "$REMOTE_HOST" \
        "cd $REMOTE_DIR && ls -1 ${DB_PREFIX}_*.db 2>/dev/null | sort" || true)
    REMOTE_COUNT=$(echo "$REMOTE_FILES" | grep -c . || echo 0)
    log "Remote backups found: $REMOTE_COUNT"

    # 3. Check file count
    if [ "$LOCAL_COUNT" -ne "$REMOTE_COUNT" ]; then
        echo "" >> "$ALERT_FILE"
        echo "WARNING: Backup count mismatch for $DB_PREFIX" >> "$ALERT_FILE"
        echo "  Local: $LOCAL_COUNT files" >> "$ALERT_FILE"
        echo "  Remote: $REMOTE_COUNT files" >> "$ALERT_FILE"
        log "WARNING: Backup count mismatch (Local: $LOCAL_COUNT, Remote: $REMOTE_COUNT)"
        OVERALL_STATUS="WARNING"
    elif [ "$LOCAL_COUNT" -gt 10 ] || [ "$REMOTE_COUNT" -gt 10 ]; then
        echo "" >> "$ALERT_FILE"
        echo "WARNING: Too many backups for $DB_PREFIX (cleanup may have failed)" >> "$ALERT_FILE"
        echo "  Local: $LOCAL_COUNT files (expected: <= 10)" >> "$ALERT_FILE"
        echo "  Remote: $REMOTE_COUNT files (expected: <= 10)" >> "$ALERT_FILE"
        log "WARNING: Too many backups (Local: $LOCAL_COUNT, Remote: $REMOTE_COUNT)"
        OVERALL_STATUS="WARNING"
    fi

    # 4. Check filename matching and detect orphan files
    log "Checking filename matching..."
    ORPHAN_DETECTED=false

    if [ "$LOCAL_FILES" != "$REMOTE_FILES" ]; then
        # Detect orphan files (files that exist only on one side)
        LOCAL_ONLY=$(comm -23 <(echo "$LOCAL_FILES") <(echo "$REMOTE_FILES"))
        REMOTE_ONLY=$(comm -13 <(echo "$LOCAL_FILES") <(echo "$REMOTE_FILES"))

        if [ -n "$LOCAL_ONLY" ]; then
            ORPHAN_DETECTED=true
            echo "" >> "$ALERT_FILE"
            echo "ERROR: Orphan files detected for $DB_PREFIX (Local only)" >> "$ALERT_FILE"
            echo "$LOCAL_ONLY" | while read -r ORPHAN_FILE; do
                echo "  - $ORPHAN_FILE" >> "$ALERT_FILE"
                log "ORPHAN: Local only: $ORPHAN_FILE"
            done
        fi

        if [ -n "$REMOTE_ONLY" ]; then
            ORPHAN_DETECTED=true
            echo "" >> "$ALERT_FILE"
            echo "ERROR: Orphan files detected for $DB_PREFIX (Remote only)" >> "$ALERT_FILE"
            echo "$REMOTE_ONLY" | while read -r ORPHAN_FILE; do
                echo "  - $ORPHAN_FILE" >> "$ALERT_FILE"
                log "ORPHAN: Remote only: $ORPHAN_FILE"
            done
        fi

        if [ "$ORPHAN_DETECTED" = true ]; then
            log "ERROR: Orphan files detected for $DB_PREFIX"
            OVERALL_STATUS="ERROR"
        fi
    fi

    # 5. CRC32 checksum verification
    log "Verifying CRC32 checksums..."
    CHECKSUM_MISMATCH=0

    for FILE in $LOCAL_FILES; do
        if echo "$REMOTE_FILES" | grep -q "^${FILE}$"; then
            # File exists in both locations, check CRC32
            LOCAL_CRC=$(cd "$LOCAL_BACKUP_DIR" && cksum "$FILE" 2>/dev/null | awk '{print $1}')
            REMOTE_CRC=$(ssh "$REMOTE_HOST" \
                "cd $REMOTE_DIR && cksum $FILE 2>/dev/null | awk '{print \$1}'")

            if [ "$LOCAL_CRC" != "$REMOTE_CRC" ]; then
                echo "" >> "$ALERT_FILE"
                echo "ERROR: CRC32 mismatch for $FILE" >> "$ALERT_FILE"
                echo "  Local:  $LOCAL_CRC" >> "$ALERT_FILE"
                echo "  Remote: $REMOTE_CRC" >> "$ALERT_FILE"
                log "ERROR: CRC32 mismatch for $FILE (Local: $LOCAL_CRC, Remote: $REMOTE_CRC)"
                CHECKSUM_MISMATCH=1
                OVERALL_STATUS="ERROR"
            fi
        fi
    done

    if [ $CHECKSUM_MISMATCH -eq 0 ] && [ "$LOCAL_FILES" = "$REMOTE_FILES" ]; then
        log "SUCCESS: All checksums match for $DB_PREFIX"
    fi

    # 6. Check last backup time
    LATEST_LOCAL=$(cd "$LOCAL_BACKUP_DIR" && ls -t ${DB_PREFIX}_*.db 2>/dev/null | head -1 || true)
    if [ -n "$LATEST_LOCAL" ]; then
        LATEST_TIME=$(stat -c %Y "$LOCAL_BACKUP_DIR/$LATEST_LOCAL" 2>/dev/null || echo 0)
        CURRENT_TIME=$(date +%s)
        AGE_HOURS=$(( ($CURRENT_TIME - $LATEST_TIME) / 3600 ))

        log "Latest backup age: $AGE_HOURS hours ($LATEST_LOCAL)"

        if [ $AGE_HOURS -gt 24 ]; then
            echo "" >> "$ALERT_FILE"
            echo "WARNING: Latest backup for $DB_PREFIX is $AGE_HOURS hours old (>24 hours)" >> "$ALERT_FILE"
            echo "  Latest: $LATEST_LOCAL" >> "$ALERT_FILE"
            log "WARNING: Latest backup is too old ($AGE_HOURS hours)"
            OVERALL_STATUS="WARNING"
        fi
    fi
done

# 7. Generate report
if [ "$OVERALL_STATUS" != "OK" ]; then
    log ""
    log "=== ALERTS DETECTED ==="
    cat "$ALERT_FILE" | tee -a "$LOG_FILE"

    # Send email alert via VPS
    ALERT_SUBJECT="[URGENT] All Databases Backup Alert"
    ALERT_BODY="Backup integrity check FAILED at $(date '+%Y-%m-%d %H:%M:%S')

$(cat "$ALERT_FILE")

Please check immediately:
- Local: /home/koshikawa/toExecUnit/backup/
- Remote: ubuntu@133.167.93.123:/home/ubuntu/sisters_backup/
- Log: /home/koshikawa/toExecUnit/logs/backup_integrity.log

---
Automated alert from All Databases Backup System"

    # Call VPS email script via SSH
    ssh "$REMOTE_HOST" \
        "/home/ubuntu/scripts/send_alert_email.sh \"$ALERT_SUBJECT\" \"$ALERT_BODY\"" \
        >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "Email alert sent successfully"
    else
        log "WARNING: Failed to send email alert"
    fi

    log "=== Backup Integrity Check Complete (WITH ALERTS) ==="
    exit 1
else
    log ""
    log "=== Backup Integrity Check Complete (OK) ==="
    echo "OK: All databases backed up and verified" > "$ALERT_FILE"

    # Summary for each database
    for DB_PREFIX in "${DB_PREFIXES[@]}"; do
        LOCAL_COUNT=$(cd "$LOCAL_BACKUP_DIR" && ls -1 ${DB_PREFIX}_*.db 2>/dev/null | wc -l || echo 0)
        echo "  - $DB_PREFIX: $LOCAL_COUNT backups" >> "$ALERT_FILE"
    done

    exit 0
fi
