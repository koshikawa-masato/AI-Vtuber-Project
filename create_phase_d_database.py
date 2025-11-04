#!/usr/bin/env python3
"""
Phase D: Database Creation Script
Creates sisters_memory.db with complete schema
"""

import sqlite3
import sys
from pathlib import Path

def create_database():
    """Create Phase D database with schema"""

    # Database path
    db_path = Path("/home/koshikawa/toExecUnit/sisters_memory.db")

    # Read SQL schema
    schema_path = Path("/home/koshikawa/toExecUnit/Phase_D_データベーススキーマ.sql")

    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        return False

    # Read schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Create database
    print(f"[INFO] Creating database: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Execute schema
        cursor.executescript(schema_sql)

        conn.commit()

        # Verify tables created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"[SUCCESS] Database created with {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Verify metadata
        cursor.execute("SELECT metadata_key, metadata_value FROM phase_d_metadata ORDER BY metadata_key")
        metadata = cursor.fetchall()

        print(f"\n[INFO] Initial metadata:")
        for key, value in metadata:
            print(f"  {key}: {value}")

        conn.close()

        print(f"\n[SUCCESS] Phase D database created successfully!")
        print(f"[INFO] Database location: {db_path}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
