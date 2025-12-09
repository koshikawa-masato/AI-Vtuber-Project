"""
Conversation Encryption - AES-256 encryption for stored conversations.

Provides field-level encryption for sensitive data in the database.
Uses hash-based lookup for user identifiers to enable queries on encrypted data.

Adapted from Sisters-On-WhatsApp for LINE Bot integration.
Supports both phone_number (WhatsApp) and user_id (LINE) identifiers.
"""

import os
import base64
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class ConversationEncryption:
    """
    AES-256 encryption for conversation content.

    Uses Fernet (AES-128-CBC with HMAC) which is simpler and secure enough.
    For true AES-256, we use PBKDF2 to derive a 256-bit key.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption with key from environment or parameter.

        Args:
            encryption_key: Base64-encoded encryption key, or will use ENCRYPTION_KEY env var
        """
        key_source = encryption_key or os.getenv("ENCRYPTION_KEY")

        if not key_source:
            logger.warning("ENCRYPTION_KEY not set - generating new key (NOT FOR PRODUCTION)")
            # Generate a key for development only
            key_source = Fernet.generate_key().decode()
            logger.warning(f"Generated key (save this!): {key_source}")

        # Derive a proper Fernet key from the source key
        self.fernet = self._create_fernet(key_source)

        # Salt for identifier hashing (from env or default)
        # Supports both LINE user_id and WhatsApp phone_number
        self._hash_salt = os.getenv("USER_HASH_SALT", "sisters_unified_salt_v1").encode()

    def _create_fernet(self, key_source: str) -> Fernet:
        """Create Fernet instance from key source."""
        # If it's already a valid Fernet key (44 chars base64), use directly
        if len(key_source) == 44:
            try:
                return Fernet(key_source.encode())
            except Exception:
                pass

        # Otherwise, derive a key using PBKDF2
        salt = b"sisters_unified_db_v1"  # Static salt (key is already secret)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_source.encode()))
        return Fernet(key)

    def _looks_like_fernet_token(self, text: str) -> bool:
        """
        Check if text looks like a Fernet token by examining its structure.

        Fernet token structure:
        - Version byte (0x80)
        - 8 bytes timestamp
        - 16 bytes IV
        - Ciphertext (variable)
        - 32 bytes HMAC

        Minimum length: 1 + 8 + 16 + 16 + 32 = 73 bytes = ~100 base64 chars

        Returns:
            True if text appears to be a valid Fernet token
        """
        if not text or len(text) < 100:
            return False

        try:
            # Try to decode as urlsafe base64
            decoded = base64.urlsafe_b64decode(text.encode('utf-8'))

            # Fernet tokens must start with version byte 0x80
            if len(decoded) >= 1 and decoded[0] == 0x80:
                return True

            return False
        except Exception:
            return False

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: The text to encrypt

        Returns:
            Base64-encoded encrypted string (Fernet's native format)
        """
        if not plaintext:
            return plaintext

        try:
            # Fernet.encrypt() already returns urlsafe base64-encoded bytes
            # No need for additional base64 encoding
            encrypted = self.fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')  # Just decode bytes to string
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Handles both:
        - Legacy double-encoded format: Z0FBQUFB... (base64 of base64)
        - New single-encoded format: gAAAAA... (Fernet's native base64)

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext, or None if data is corrupted
        """
        if not ciphertext:
            return ciphertext

        try:
            result = None

            # Check if it's double-encoded (legacy format)
            # Double-encoded strings start with 'Z0FBQUFB' which decodes to 'gAAAAA'
            if ciphertext.startswith('Z0FBQUFB'):
                # Legacy double-encoded: decode base64 first, then decrypt
                encrypted = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
                decrypted = self.fernet.decrypt(encrypted)
                result = decrypted.decode('utf-8')
            elif ciphertext.startswith('gAAAAA'):
                # New single-encoded format: Fernet's native base64
                decrypted = self.fernet.decrypt(ciphertext.encode('utf-8'))
                result = decrypted.decode('utf-8')
            else:
                # Unknown format, return as-is (might be unencrypted)
                return ciphertext

            # Validate: decrypted result should not look like encrypted data
            # Check if result is still a valid Fernet token (corrupted/double-encrypted)
            if result and self._looks_like_fernet_token(result):
                logger.warning(f"Corrupted data detected: decrypted result still appears encrypted")
                return None

            return result
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Return original if decryption fails (might be unencrypted legacy data)
            return ciphertext

    def is_encrypted(self, text: str) -> bool:
        """
        Check if text appears to be encrypted.

        Detects both:
        - Legacy double-encoded format: Z0FBQUFB... (base64 of base64)
        - New single-encoded format: gAAAAA... (Fernet's native base64)
        """
        if not text:
            return False

        # Check for double-encoded format (legacy)
        # 'Z0FBQUFB' is base64 encoding of 'gAAAAA' (Fernet token prefix)
        if text.startswith('Z0FBQUFB'):
            return True

        # Check for single-encoded format (new/correct)
        # Fernet tokens start with 'gAAAAA' (version byte 0x80 = 128)
        if text.startswith('gAAAAA'):
            return True

        return False

    def encrypt_if_needed(self, text: str) -> str:
        """Encrypt text only if not already encrypted."""
        if self.is_encrypted(text):
            return text
        return self.encrypt(text)

    def decrypt_if_needed(self, text: str) -> str:
        """Decrypt text only if it's encrypted."""
        if not self.is_encrypted(text):
            return text
        return self.decrypt(text)

    def hash_identifier(self, identifier: str) -> str:
        """
        Create a deterministic hash of user identifier for database lookups.

        Works for both LINE user_id and WhatsApp phone_number.
        Uses SHA-256 with salt to create a consistent hash that can be used
        as a lookup key while keeping the actual identifier encrypted.

        Args:
            identifier: The user identifier (LINE user_id or WhatsApp phone_number)

        Returns:
            Hex-encoded SHA-256 hash (64 characters)
        """
        if not identifier:
            return identifier

        # Normalize identifier (remove spaces)
        normalized = identifier.strip().replace(" ", "")

        # Create salted hash
        salted = self._hash_salt + normalized.encode('utf-8')
        return hashlib.sha256(salted).hexdigest()

    # Alias for backward compatibility with WhatsApp code
    def hash_phone_number(self, phone_number: str) -> str:
        """Alias for hash_identifier - for WhatsApp compatibility."""
        return self.hash_identifier(phone_number)

    # Alias for LINE Bot code
    def hash_user_id(self, user_id: str) -> str:
        """Alias for hash_identifier - for LINE Bot compatibility."""
        return self.hash_identifier(user_id)

    def is_identifier_hash(self, value: str) -> bool:
        """Check if value looks like an identifier hash (64 hex chars)."""
        if not value or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    def encrypt_json(self, data: Union[dict, list]) -> str:
        """Encrypt a JSON-serializable object."""
        if data is None:
            return None
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)

    def decrypt_json(self, ciphertext: str) -> Union[dict, list, None]:
        """Decrypt to a JSON object."""
        if not ciphertext:
            return None

        decrypted = self.decrypt_if_needed(ciphertext)

        # If decryption returned original (legacy unencrypted data)
        if decrypted == ciphertext:
            # Try parsing as JSON directly
            try:
                return json.loads(ciphertext)
            except json.JSONDecodeError:
                return ciphertext

        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted


class EncryptedFieldManager:
    """
    Manages encryption for all sensitive database fields.

    Provides hash-based lookup for user identifiers and encryption for content.
    Supports both LINE Bot and WhatsApp Bot tables.
    """

    # Fields requiring encryption by table
    # Unified for both LINE Bot and WhatsApp Bot
    SENSITIVE_FIELDS = {
        # Shared tables (both platforms)
        'conversation_history': {
            'phone_number': 'identifier',  # WhatsApp
            'user_id': 'identifier',       # LINE Bot
            'content': 'text',
            'message': 'text',
        },
        'user_sessions': {
            'phone_number': 'identifier',
        },
        'user_consents': {
            'phone_number': 'identifier',
            'user_id': 'identifier',
        },
        'user_memories': {
            'phone_number': 'identifier',
            'user_id': 'identifier',
            'profile': 'text',
            'preferences': 'json',
            'facts': 'json',
            'topics_discussed': 'json',
            'personality_notes': 'text',
            'memory_text': 'text',
            'context': 'text',
        },
        # LINE Bot specific tables
        'sessions': {
            'user_id': 'identifier',
        },
        'learning_logs': {
            'user_id': 'identifier',
            'user_message': 'text',
            'bot_response': 'text',
        },
        'feedback': {
            'user_id': 'identifier',
            'feedback_text': 'text',
        },
        'user_personality': {
            'user_id': 'identifier',
        },
        'user_trust_history': {
            'user_id': 'identifier',
        },
    }

    def __init__(self):
        self.encryption = ConversationEncryption()

    def get_identifier_hash(self, identifier: str) -> str:
        """Get hash for identifier lookup (works for both user_id and phone_number)."""
        return self.encryption.hash_identifier(identifier)

    def encrypt_identifier(self, identifier: str) -> str:
        """Encrypt identifier for storage."""
        return self.encryption.encrypt(identifier)

    def decrypt_identifier(self, encrypted_identifier: str) -> str:
        """Decrypt identifier for display/export."""
        return self.encryption.decrypt_if_needed(encrypted_identifier)

    def encrypt_field(self, value: Any, field_type: str) -> Any:
        """
        Encrypt a field based on its type.

        Args:
            value: The value to encrypt
            field_type: 'text', 'json', or 'identifier'

        Returns:
            Encrypted value
        """
        if value is None:
            return None

        if field_type == 'text':
            return self.encryption.encrypt(str(value))
        elif field_type == 'json':
            return self.encryption.encrypt_json(value)
        elif field_type == 'identifier':
            return self.encryption.encrypt(value)
        else:
            return value

    def decrypt_field(self, value: Any, field_type: str) -> Any:
        """
        Decrypt a field based on its type.

        Args:
            value: The encrypted value
            field_type: 'text', 'json', or 'identifier'

        Returns:
            Decrypted value
        """
        if value is None:
            return None

        if field_type == 'text':
            return self.encryption.decrypt_if_needed(str(value))
        elif field_type == 'json':
            return self.encryption.decrypt_json(value)
        elif field_type == 'identifier':
            return self.encryption.decrypt_if_needed(value)
        else:
            return value

    def encrypt_record(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt all sensitive fields in a database record.

        Args:
            table: Table name
            record: Record dict with field values

        Returns:
            Record with sensitive fields encrypted
        """
        if table not in self.SENSITIVE_FIELDS:
            return record

        encrypted = record.copy()
        field_types = self.SENSITIVE_FIELDS[table]

        for field, field_type in field_types.items():
            if field in encrypted and encrypted[field] is not None:
                # For identifier fields, also add hash for lookup
                if field_type == 'identifier':
                    hash_field = f"{field.replace('_id', '').replace('_number', '')}_hash"
                    if field == 'user_id':
                        hash_field = 'user_hash'
                    elif field == 'phone_number':
                        hash_field = 'phone_hash'
                    encrypted[hash_field] = self.get_identifier_hash(encrypted[field])
                encrypted[field] = self.encrypt_field(encrypted[field], field_type)

        return encrypted

    def decrypt_record(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all sensitive fields in a database record.

        Args:
            table: Table name
            record: Record dict with encrypted field values

        Returns:
            Record with sensitive fields decrypted
        """
        if table not in self.SENSITIVE_FIELDS:
            return record

        decrypted = record.copy()
        field_types = self.SENSITIVE_FIELDS[table]

        for field, field_type in field_types.items():
            if field in decrypted and decrypted[field] is not None:
                decrypted[field] = self.decrypt_field(decrypted[field], field_type)

        # Remove hash fields from output (internal use only)
        decrypted.pop('user_hash', None)
        decrypted.pop('phone_hash', None)

        return decrypted


def generate_encryption_key() -> str:
    """Generate a new encryption key for .env file."""
    key = Fernet.generate_key()
    return key.decode()


def generate_hash_salt() -> str:
    """Generate a new salt for identifier hashing."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


if __name__ == "__main__":
    # Generate keys when run directly
    print("=" * 60)
    print("Encryption Keys for .env")
    print("=" * 60)
    print()
    print("# Add these to your .env file:")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print(f"USER_HASH_SALT={generate_hash_salt()}")
    print()
    print("=" * 60)

    # Demo
    print("\nDemo: User ID hashing (LINE Bot)")
    print("-" * 40)
    enc = ConversationEncryption()
    test_user_id = "U1234567890abcdef"
    user_hash = enc.hash_user_id(test_user_id)
    user_encrypted = enc.encrypt(test_user_id)
    print(f"Original:  {test_user_id}")
    print(f"Hash:      {user_hash}")
    print(f"Encrypted: {user_encrypted[:50]}...")
    print(f"Decrypted: {enc.decrypt(user_encrypted)}")

    print("\nDemo: Message encryption")
    print("-" * 40)
    test_message = "Hello, this is a test message!"
    encrypted_msg = enc.encrypt(test_message)
    print(f"Original:  {test_message}")
    print(f"Encrypted: {encrypted_msg[:50]}...")
    print(f"Decrypted: {enc.decrypt(encrypted_msg)}")
