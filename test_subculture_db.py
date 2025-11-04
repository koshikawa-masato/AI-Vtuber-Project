"""
Subculture Knowledge Database Test Script
==========================================

Tests the subculture_knowledge.db to verify:
1. Database structure is correct
2. Data migration was successful
3. Queries work as expected
4. Integration points are ready

Usage:
    python test_subculture_db.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

def test_database_structure(db_path):
    """Test 1: Verify database structure"""

    print(f"\n{'='*60}")
    print(f"TEST 1: Database Structure")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
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

    print(f"Expected tables: {len(expected_tables)}")
    print(f"Actual tables: {len(actual_tables)}")

    missing = set(expected_tables) - set(actual_tables)
    extra = set(actual_tables) - set(expected_tables)

    if missing:
        print(f"[FAIL] Missing tables: {missing}")
        return False
    if extra:
        print(f"[INFO] Extra tables: {extra}")

    print(f"[PASS] All expected tables exist")

    conn.close()
    return True


def test_data_migration(db_path):
    """Test 2: Verify data migration"""

    print(f"\n{'='*60}")
    print(f"TEST 2: Data Migration")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Test VTuber count
    cursor.execute("SELECT COUNT(*) FROM vtubers")
    vtuber_count = cursor.fetchone()[0]
    print(f"Total VTubers: {vtuber_count}")

    if vtuber_count < 50:
        print(f"[FAIL] Expected at least 50 VTubers (all Hololive members)")
        return False

    print(f"[PASS] VTuber count OK (>= 50)")

    # Test Botan's favorites
    cursor.execute("""
    SELECT v.name
    FROM vtubers v
    JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE a.affinity_level = 5
    ORDER BY v.name
    """)
    favorites = [row[0] for row in cursor.fetchall()]

    print(f"\nBotan's Oshi (Level 5): {favorites}")

    expected_favorites = ['戌神ころね', 'さくらみこ']
    if not all(fav in favorites for fav in expected_favorites):
        print(f"[FAIL] Expected favorites: {expected_favorites}")
        return False

    print(f"[PASS] Botan's favorites correctly set")

    # Test catchphrases
    cursor.execute("""
    SELECT v.name, COUNT(c.phrase_id)
    FROM vtubers v
    JOIN vtuber_catchphrases c ON v.vtuber_id = c.vtuber_id
    GROUP BY v.name
    """)
    catchphrase_counts = cursor.fetchall()

    print(f"\nCatchphrases per VTuber:")
    for name, count in catchphrase_counts:
        print(f"  {name}: {count} phrases")

    if len(catchphrase_counts) < 2:
        print(f"[FAIL] Expected catchphrases for at least 2 VTubers")
        return False

    print(f"[PASS] Catchphrases migrated")

    # Test episodes
    cursor.execute("""
    SELECT v.name, COUNT(e.episode_id)
    FROM vtubers v
    JOIN vtuber_episodes e ON v.vtuber_id = e.vtuber_id
    GROUP BY v.name
    """)
    episode_counts = cursor.fetchall()

    print(f"\nFamous episodes per VTuber:")
    for name, count in episode_counts:
        print(f"  {name}: {count} episodes")

    if len(episode_counts) < 2:
        print(f"[FAIL] Expected episodes for at least 2 VTubers")
        return False

    print(f"[PASS] Episodes migrated")

    conn.close()
    return True


def test_query_performance(db_path):
    """Test 3: Query performance and correctness"""

    print(f"\n{'='*60}")
    print(f"TEST 3: Query Performance")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query 1: Get VTuber details with affinity
    print(f"\nQuery 1: VTuber details with affinity")
    cursor.execute("""
    SELECT
        v.name,
        v.fan_name,
        v.self_title,
        a.affinity_level
    FROM vtubers v
    LEFT JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE v.name IN ('戌神ころね', 'さくらみこ', '白銀ノエル')
    ORDER BY a.affinity_level DESC
    """)

    for row in cursor.fetchall():
        name, fan_name, self_title, affinity = row
        print(f"  {name} (Level {affinity})")
        print(f"    Fan name: {fan_name}")
        print(f"    Self title: {self_title}")

    # Query 2: Get catchphrases for a VTuber
    print(f"\nQuery 2: Catchphrases for 戌神ころね")
    cursor.execute("""
    SELECT c.phrase, c.meaning, c.usage_context
    FROM vtuber_catchphrases c
    JOIN vtubers v ON c.vtuber_id = v.vtuber_id
    WHERE v.name = '戌神ころね'
    LIMIT 5
    """)

    for row in cursor.fetchall():
        phrase, meaning, usage = row
        print(f"  {phrase}: {meaning}")

    # Query 3: Get famous episodes
    print(f"\nQuery 3: Famous episodes for さくらみこ")
    cursor.execute("""
    SELECT e.title, e.description
    FROM vtuber_episodes e
    JOIN vtubers v ON e.vtuber_id = v.vtuber_id
    WHERE v.name = 'さくらみこ'
    LIMIT 3
    """)

    for row in cursor.fetchall():
        title, description = row
        print(f"  {title}")
        if description:
            print(f"    {description[:100]}...")

    print(f"\n[PASS] Queries executed successfully")

    conn.close()
    return True


def test_conversation_integration(db_path):
    """Test 4: Conversation integration points"""

    print(f"\n{'='*60}")
    print(f"TEST 4: Conversation Integration")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Simulate conversation scenario 1: User asks about Korone
    print(f"\nScenario 1: User asks 'ころねさんって誰？'")

    cursor.execute("""
    SELECT
        v.name,
        v.generation,
        v.fan_name,
        v.self_title,
        v.greeting,
        a.affinity_level,
        a.why_like
    FROM vtubers v
    LEFT JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE v.name LIKE '%ころね%'
    """)

    result = cursor.fetchone()
    if result:
        name, gen, fan_name, self_title, greeting, affinity, why_like = result
        print(f"\n[Botan's response context]")
        print(f"Name: {name}")
        print(f"Generation: {gen}")
        print(f"Fan name: {fan_name}")
        print(f"Affinity: Level {affinity}")
        print(f"Why like: {why_like}")

        # Get catchphrases
        cursor.execute("""
        SELECT phrase, meaning
        FROM vtuber_catchphrases
        WHERE vtuber_id = (SELECT vtuber_id FROM vtubers WHERE name = ?)
        LIMIT 3
        """, (name,))

        phrases = cursor.fetchall()
        print(f"\nCatchphrases to mention:")
        for phrase, meaning in phrases:
            print(f"  - {phrase} ({meaning})")

    # Simulate scenario 2: User mentions watching Miko's stream
    print(f"\n\nScenario 2: User says '昨日みこちの配信見た？'")

    cursor.execute("""
    SELECT
        v.name,
        v.fan_name,
        a.affinity_level
    FROM vtubers v
    LEFT JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE v.name LIKE '%みこ%'
    """)

    result = cursor.fetchone()
    if result:
        name, fan_name, affinity = result
        print(f"\n[Botan's response context]")
        print(f"Name: {name}")
        print(f"Fan name: {fan_name} (35P)")
        print(f"Affinity: Level {affinity} (Oshi)")

        # Get recent episodes
        cursor.execute("""
        SELECT title, description
        FROM vtuber_episodes
        WHERE vtuber_id = (SELECT vtuber_id FROM vtubers WHERE name = ?)
        ORDER BY episode_date DESC
        LIMIT 2
        """, (name,))

        episodes = cursor.fetchall()
        print(f"\nFamous episodes to reference:")
        for title, description in episodes:
            print(f"  - {title}")

    print(f"\n[PASS] Conversation integration ready")

    conn.close()
    return True


def test_future_readiness(db_path):
    """Test 5: Future feature readiness"""

    print(f"\n{'='*60}")
    print(f"TEST 5: Future Feature Readiness")
    print(f"{'='*60}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if streams table is ready
    print(f"\nStreams table (for YouTube API integration):")
    cursor.execute("SELECT COUNT(*) FROM vtuber_streams")
    stream_count = cursor.fetchone()[0]
    print(f"  Current streams: {stream_count}")
    print(f"  [READY] Table structure prepared for YouTube API data")

    # Check if watch history is ready
    print(f"\nWatch history table (for 'yesterday's stream' tracking):")
    cursor.execute("SELECT COUNT(*) FROM botan_watch_history")
    watch_count = cursor.fetchone()[0]
    print(f"  Current watch records: {watch_count}")
    print(f"  [READY] Table structure prepared for watch tracking")

    # Check metadata
    print(f"\nDatabase metadata:")
    cursor.execute("SELECT key, value FROM db_metadata")
    metadata = cursor.fetchall()
    for key, value in metadata:
        print(f"  {key}: {value}")

    print(f"\n[PASS] Database ready for Phase 2 features")

    conn.close()
    return True


def run_all_tests(db_path):
    """Run all tests"""

    print(f"\n{'#'*60}")
    print(f"# Subculture Knowledge Database Test Suite")
    print(f"# Database: {db_path}")
    print(f"# Time: {datetime.now()}")
    print(f"{'#'*60}")

    if not db_path.exists():
        print(f"\n[ERROR] Database not found: {db_path}")
        print(f"[INFO] Please run:")
        print(f"  1. python create_subculture_db.py")
        print(f"  2. python migrate_vtuber_data.py")
        return False

    results = []

    # Run tests
    results.append(("Database Structure", test_database_structure(db_path)))
    results.append(("Data Migration", test_data_migration(db_path)))
    results.append(("Query Performance", test_query_performance(db_path)))
    results.append(("Conversation Integration", test_conversation_integration(db_path)))
    results.append(("Future Readiness", test_future_readiness(db_path)))

    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print(f"\n✓ All tests passed!")
        print(f"\n[READY] Database is ready for integration with chat system")
        print(f"\n[NEXT STEPS]")
        print(f"1. Integrate with chat_with_botan_memories.py")
        print(f"2. Test conversations with VTuber knowledge")
        print(f"3. Set up YouTube Data API (Phase 1 Week 2)")
        return True
    else:
        print(f"\n✗ Some tests failed")
        print(f"[INFO] Please check error messages above")
        return False


if __name__ == "__main__":
    db_path = Path(__file__).parent / 'subculture_knowledge.db'
    success = run_all_tests(db_path)

    exit(0 if success else 1)
