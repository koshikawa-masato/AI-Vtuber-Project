"""
Database Test Suite
===================

Tests for database creation, migration, and data integrity.

Usage:
    python -m botan_subculture.tests.test_database
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH
from botan_subculture.database.create_db import create_database, verify_database
from botan_subculture.database.migrate_data import migrate_vtuber_data


def test_database_creation():
    """Test 1: Database creation"""
    print("\n" + "=" * 60)
    print("Test 1: Database Creation")
    print("=" * 60)

    if DB_PATH.exists():
        print(f"[INFO] Removing existing database: {DB_PATH}")
        DB_PATH.unlink()

    create_database(str(DB_PATH))

    if DB_PATH.exists():
        print("[PASS] Database created successfully")
        return True
    else:
        print("[FAIL] Database creation failed")
        return False


def test_database_schema():
    """Test 2: Database schema verification"""
    print("\n" + "=" * 60)
    print("Test 2: Database Schema Verification")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Expected tables
    expected_tables = [
        'vtubers',
        'vtuber_streams',
        'vtuber_catchphrases',
        'vtuber_episodes',
        'botan_vtuber_affinity',
        'botan_watch_history',
        'artists',
        'light_novels',
        'db_metadata'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    actual_tables = [row[0] for row in cursor.fetchall()]

    print(f"[INFO] Expected {len(expected_tables)} tables")
    print(f"[INFO] Found {len(actual_tables)} tables")

    missing = set(expected_tables) - set(actual_tables)
    extra = set(actual_tables) - set(expected_tables)

    if missing:
        print(f"[WARN] Missing tables: {missing}")

    if extra:
        print(f"[INFO] Extra tables: {extra}")

    conn.close()

    if not missing:
        print("[PASS] All expected tables exist")
        return True
    else:
        print("[FAIL] Missing required tables")
        return False


def test_data_migration():
    """Test 3: Data migration from JSON"""
    print("\n" + "=" * 60)
    print("Test 3: Data Migration")
    print("=" * 60)

    try:
        migrate_vtuber_data(str(DB_PATH))
        print("[PASS] Data migration completed")

        # Verify migrated data
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vtubers")
        vtuber_count = cursor.fetchone()[0]
        print(f"[INFO] Migrated {vtuber_count} VTubers")

        cursor.execute("SELECT COUNT(*) FROM botan_vtuber_affinity WHERE affinity_level = 5")
        favorites_count = cursor.fetchone()[0]
        print(f"[INFO] Found {favorites_count} favorites (affinity level 5)")

        cursor.execute("SELECT COUNT(*) FROM vtuber_catchphrases")
        phrases_count = cursor.fetchone()[0]
        print(f"[INFO] Found {phrases_count} catchphrases")

        conn.close()

        if vtuber_count > 0:
            print("[PASS] Data migration successful")
            return True
        else:
            print("[FAIL] No data migrated")
            return False

    except Exception as e:
        print(f"[FAIL] Migration failed: {e}")
        return False


def test_affinity_system():
    """Test 4: Affinity system verification"""
    print("\n" + "=" * 60)
    print("Test 4: Affinity System")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check affinity levels
    cursor.execute("""
    SELECT
        v.name,
        a.affinity_level,
        a.why_like
    FROM vtubers v
    LEFT JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE a.affinity_level = 5
    ORDER BY v.name
    """)

    favorites = cursor.fetchall()

    print(f"[INFO] Botan's Favorites (Affinity Level 5):")
    for name, level, why in favorites:
        print(f"  - {name}: {why[:50] if why else 'N/A'}...")

    conn.close()

    if len(favorites) >= 2:  # Expecting at least Korone and Miko
        print("[PASS] Affinity system working correctly")
        return True
    else:
        print("[WARN] Expected at least 2 favorites")
        return False


def test_content_restriction_fields():
    """Test 5: Content restriction fields"""
    print("\n" + "=" * 60)
    print("Test 5: Content Restriction Fields")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if restriction fields exist in vtuber_streams
    cursor.execute("PRAGMA table_info(vtuber_streams)")
    columns = [row[1] for row in cursor.fetchall()]

    required_fields = [
        'is_member_only',
        'is_clip_prohibited',
        'content_visibility',
        'is_ongoing',
        'stream_end_time'
    ]

    missing_fields = [f for f in required_fields if f not in columns]

    if missing_fields:
        print(f"[FAIL] Missing fields: {missing_fields}")
        conn.close()
        return False

    print("[INFO] All content restriction fields present:")
    for field in required_fields:
        print(f"  - {field}")

    conn.close()
    print("[PASS] Content restriction fields verified")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("Botan Subculture Database Test Suite")
    print("=" * 60)

    tests = [
        test_database_creation,
        test_database_schema,
        test_data_migration,
        test_affinity_system,
        test_content_restriction_fields
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
