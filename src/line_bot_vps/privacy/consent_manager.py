"""
Consent Manager - LINE Bot version

Track and manage user consent for data processing.
Supports Japan's APPI (Act on the Protection of Personal Information).
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor

from .policy_messages import PrivacyPolicyMessages
from .encryption import ConversationEncryption

logger = logging.getLogger(__name__)


class ConsentStatus(Enum):
    """User consent status."""
    PENDING = "pending"       # Not yet responded
    GRANTED = "granted"       # User agreed
    DECLINED = "declined"     # User declined
    WITHDRAWN = "withdrawn"   # User withdrew consent (deleted data)


class ConsentManager:
    """Manage user consent for data processing (LINE Bot version)."""

    def __init__(self):
        self.connection_params = {
            "host": os.getenv("POSTGRES_HOST", "162.43.4.11"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "sisters"),
            "password": os.getenv("POSTGRES_PASSWORD", "sistersSafe2024"),
            "database": os.getenv("POSTGRES_DB", "sisters_on_whatsapp"),
        }
        self.encryption = ConversationEncryption()

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.connection_params, connect_timeout=10)

    def ensure_table_exists(self):
        """Create user_consents table if not exists."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Add LINE Bot specific columns if not exists
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_consents' AND column_name = 'user_hash') THEN
                    ALTER TABLE user_consents ADD COLUMN user_hash VARCHAR(64);
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_consents_user_hash ON user_consents(user_hash);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_consents' AND column_name = 'user_id') THEN
                    ALTER TABLE user_consents ADD COLUMN user_id VARCHAR(255);
                END IF;
            END $$;
        """)

        conn.commit()
        conn.close()
        logger.info("user_consents table ready for LINE Bot")

    def get_user_consent(self, user_id: str) -> Optional[Dict]:
        """Get user's consent record."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try by user_hash (LINE Bot records)
        cursor.execute("""
            SELECT * FROM user_consents WHERE user_hash = %s
        """, (user_hash,))
        result = cursor.fetchone()

        conn.close()
        return dict(result) if result else None

    def create_pending_consent(self, user_id: str, language: str = "ja") -> Dict:
        """Create a pending consent record for new user."""
        user_hash = self.encryption.hash_user_id(user_id)
        encrypted_user_id = self.encryption.encrypt(user_id)

        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO user_consents (
                user_hash, user_id, phone_number, region, status, language,
                policy_url_shown, platform, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'line', %s)
            ON CONFLICT (user_hash) DO UPDATE SET
                last_reminded_at = CURRENT_TIMESTAMP
            RETURNING *
        """, (
            user_hash,
            encrypted_user_id,
            encrypted_user_id,  # Use encrypted user_id for phone_number field
            "japan",
            ConsentStatus.PENDING.value,
            language,
            PrivacyPolicyMessages.POLICY_URL,
            datetime.now()
        ))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        logger.info(f"Created pending consent for LINE user {user_hash[:8]}...")
        return dict(result)

    def grant_consent(self, user_id: str) -> bool:
        """Record user's consent."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_consents
            SET status = %s,
                consent_given_at = CURRENT_TIMESTAMP,
                consent_method = 'line_message'
            WHERE user_hash = %s
            RETURNING id
        """, (ConsentStatus.GRANTED.value, user_hash))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if result:
            logger.info(f"Consent granted for LINE user {user_hash[:8]}...")
            return True
        return False

    def decline_consent(self, user_id: str) -> bool:
        """Record user's decline."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_consents
            SET status = %s,
                consent_withdrawn_at = CURRENT_TIMESTAMP
            WHERE user_hash = %s
            RETURNING id
        """, (ConsentStatus.DECLINED.value, user_hash))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if result:
            logger.info(f"Consent declined for LINE user {user_hash[:8]}...")
            return True
        return False

    def withdraw_consent(self, user_id: str) -> bool:
        """Record consent withdrawal (for data deletion)."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_consents
            SET status = %s,
                consent_withdrawn_at = CURRENT_TIMESTAMP,
                data_deletion_requested_at = CURRENT_TIMESTAMP
            WHERE user_hash = %s
            RETURNING id
        """, (ConsentStatus.WITHDRAWN.value, user_hash))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if result:
            logger.info(f"Consent withdrawn for LINE user {user_hash[:8]}...")
            return True
        return False

    def has_valid_consent(self, user_id: str) -> bool:
        """Check if user has valid consent."""
        consent = self.get_user_consent(user_id)

        if not consent:
            return False

        return consent["status"] == ConsentStatus.GRANTED.value

    def needs_consent(self, user_id: str) -> bool:
        """Check if user needs to provide consent."""
        consent = self.get_user_consent(user_id)

        if not consent:
            return True

        return consent["status"] in [ConsentStatus.PENDING.value, ConsentStatus.DECLINED.value]

    def record_data_deletion(self, user_id: str) -> bool:
        """Record that user's data has been deleted."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_consents
            SET data_deleted_at = CURRENT_TIMESTAMP,
                metadata = COALESCE(metadata, '{}'::jsonb) || '{"deletion_completed": true}'::jsonb
            WHERE user_hash = %s
            RETURNING id
        """, (user_hash,))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        return result is not None

    def delete_user_data(self, user_id: str) -> Dict:
        """Delete all user data from all tables."""
        user_hash = self.encryption.hash_user_id(user_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        deleted_counts = {}

        # Delete from each table
        tables = [
            ("conversation_history", "user_hash"),
            ("user_sessions", "user_hash"),
            ("user_memories", "user_hash"),
            ("learning_logs", "user_hash"),
            ("feedback", "user_hash"),
        ]

        for table, column in tables:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", (user_hash,))
                deleted_counts[table] = cursor.rowcount
            except Exception as e:
                logger.warning(f"Error deleting from {table}: {e}")
                deleted_counts[table] = 0

        conn.commit()
        conn.close()

        # Record the deletion
        self.record_data_deletion(user_id)

        logger.info(f"Deleted data for LINE user {user_hash[:8]}...: {deleted_counts}")
        return deleted_counts

    def get_consent_statistics(self) -> Dict:
        """Get consent statistics for compliance reporting."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                platform,
                status,
                COUNT(*) as count
            FROM user_consents
            GROUP BY platform, status
            ORDER BY platform, status
        """)

        results = cursor.fetchall()
        conn.close()

        stats = {}
        for row in results:
            platform = row["platform"] or "unknown"
            if platform not in stats:
                stats[platform] = {}
            stats[platform][row["status"]] = row["count"]

        return stats
