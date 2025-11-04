"""
VTuber Data Migration Script
=============================

Migrates data from hololive_vtuber_knowledge.json to subculture_knowledge.db

This script performs Phase 1 data migration:
1. Import VTuber master data (all Hololive members)
2. Import detailed info for Botan's favorites (Korone, Miko)
3. Set affinity levels
4. Import catchphrases and famous episodes

Usage:
    python migrate_vtuber_data.py

Requirements:
    - hololive_vtuber_knowledge.json must exist
    - subculture_knowledge.db must be created first
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def load_json_knowledge(json_path='hololive_vtuber_knowledge.json'):
    """Load VTuber knowledge from JSON file"""

    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {json_path}")

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    print(f"[OK] Loaded knowledge from: {json_path}")
    return data


def migrate_vtuber_master_data(conn, knowledge):
    """Migrate VTuber master data from all generations"""

    cursor = conn.cursor()
    hololive = knowledge.get('hololive', {})
    generations = hololive.get('generations', {})

    total_inserted = 0

    print(f"\n[INFO] Migrating VTuber master data...")

    for gen_name, members in generations.items():
        print(f"[INFO] Processing {gen_name}...")

        for member in members:
            name = member.get('name')
            if not name:
                continue

            # Insert VTuber
            cursor.execute("""
            INSERT OR IGNORE INTO vtubers (
                name,
                generation,
                fan_name,
                fan_name_en,
                fan_individual,
                fan_mark,
                self_title,
                nickname
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                gen_name,
                member.get('fan_name'),
                member.get('fan_name_en'),
                member.get('fan_individual'),
                member.get('fan_mark'),
                member.get('self_title'),
                member.get('nickname')
            ))

            if cursor.rowcount > 0:
                total_inserted += 1

    conn.commit()
    print(f"[OK] Inserted {total_inserted} VTubers")

    return total_inserted


def migrate_botan_favorites(conn, knowledge):
    """Migrate detailed information for Botan's favorite VTubers"""

    cursor = conn.cursor()
    hololive = knowledge.get('hololive', {})
    favorites = hololive.get('botan_favorites', [])

    print(f"\n[INFO] Migrating Botan's favorite VTubers...")

    for favorite in favorites:
        name = favorite.get('name')
        if not name:
            continue

        print(f"[INFO] Processing favorite: {name}")

        # Update VTuber details
        cursor.execute("""
        UPDATE vtubers SET
            self_title = ?,
            nickname = ?,
            fan_name = ?,
            fan_mark = ?,
            greeting = ?
        WHERE name = ?
        """, (
            favorite.get('self_title'),
            favorite.get('nickname'),
            favorite.get('fan_name'),
            favorite.get('fan_mark'),
            favorite.get('greeting'),
            name
        ))

        # Get vtuber_id
        cursor.execute("SELECT vtuber_id FROM vtubers WHERE name = ?", (name,))
        result = cursor.fetchone()
        if not result:
            print(f"[WARNING] VTuber not found: {name}")
            continue

        vtuber_id = result[0]

        # Insert catchphrases
        catchphrases = favorite.get('catchphrases', [])
        for phrase_data in catchphrases:
            cursor.execute("""
            INSERT OR IGNORE INTO vtuber_catchphrases (
                vtuber_id,
                phrase,
                meaning,
                usage_context
            ) VALUES (?, ?, ?, ?)
            """, (
                vtuber_id,
                phrase_data.get('phrase'),
                phrase_data.get('meaning'),
                phrase_data.get('usage')
            ))

        print(f"[OK] Inserted {len(catchphrases)} catchphrases for {name}")

        # Insert famous episodes
        episodes = favorite.get('famous_episodes', [])
        for episode_data in episodes:
            cursor.execute("""
            INSERT OR IGNORE INTO vtuber_episodes (
                vtuber_id,
                title,
                episode_date,
                description,
                viral_level
            ) VALUES (?, ?, ?, ?, ?)
            """, (
                vtuber_id,
                episode_data.get('title'),
                episode_data.get('date'),
                episode_data.get('description'),
                5  # Viral level high for famous episodes
            ))

        print(f"[OK] Inserted {len(episodes)} episodes for {name}")

        # Set affinity level (5 for Oshi - favorite)
        # NOTE: Botan watches ALL streams for ALL members
        # Affinity = preference (how much she likes), not knowledge level
        cursor.execute("""
        INSERT OR REPLACE INTO botan_vtuber_affinity (
            vtuber_id,
            affinity_level,
            why_like
        ) VALUES (?, ?, ?)
        """, (
            vtuber_id,
            5,  # Oshi level (favorite)
            favorite.get('botan_comment')
        ))

        print(f"[OK] Set affinity level 5 (Oshi/Favorite) for {name}")

    conn.commit()
    print(f"[OK] Migrated {len(favorites)} favorite VTubers")

    return len(favorites)


def set_default_affinity_levels(conn):
    """Set default affinity levels for all VTubers"""

    cursor = conn.cursor()

    print(f"\n[INFO] Setting default affinity levels...")

    # Get all VTubers without affinity set
    cursor.execute("""
    SELECT vtuber_id, name, generation FROM vtubers
    WHERE vtuber_id NOT IN (SELECT vtuber_id FROM botan_vtuber_affinity)
    """)

    vtubers = cursor.fetchall()

    for vtuber_id, name, generation in vtubers:
        # Default affinity: 3 (Neutral positive preference)
        # NOTE: Botan watches ALL members' ALL content
        # This is NOT about knowledge - she knows EVERYTHING
        # This is about PREFERENCE - how much she likes them
        cursor.execute("""
        INSERT INTO botan_vtuber_affinity (
            vtuber_id,
            affinity_level
        ) VALUES (?, ?)
        """, (
            vtuber_id,
            3  # Neutral positive (likes them, not Oshi level)
        ))

    conn.commit()
    print(f"[OK] Set default affinity for {len(vtubers)} VTubers")

    return len(vtubers)


def verify_migration(conn):
    """Verify migration results"""

    cursor = conn.cursor()

    print(f"\n[INFO] Verifying migration...")

    # Count VTubers
    cursor.execute("SELECT COUNT(*) FROM vtubers")
    vtuber_count = cursor.fetchone()[0]
    print(f"[OK] Total VTubers: {vtuber_count}")

    # Count by affinity level
    cursor.execute("""
    SELECT affinity_level, COUNT(*)
    FROM botan_vtuber_affinity
    GROUP BY affinity_level
    ORDER BY affinity_level DESC
    """)
    affinity_counts = cursor.fetchall()
    print(f"[OK] Affinity distribution:")
    affinity_names = {5: 'Oshi', 4: 'Regular', 3: 'Occasional', 2: 'Know', 1: 'Heard'}
    for level, count in affinity_counts:
        print(f"    Level {level} ({affinity_names.get(level, 'Unknown')}): {count}")

    # Count catchphrases
    cursor.execute("SELECT COUNT(*) FROM vtuber_catchphrases")
    phrase_count = cursor.fetchone()[0]
    print(f"[OK] Total catchphrases: {phrase_count}")

    # Count episodes
    cursor.execute("SELECT COUNT(*) FROM vtuber_episodes")
    episode_count = cursor.fetchone()[0]
    print(f"[OK] Total episodes: {episode_count}")

    # Show Botan's favorites
    cursor.execute("""
    SELECT v.name, a.affinity_level, a.why_like
    FROM vtubers v
    JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
    WHERE a.affinity_level = 5
    ORDER BY v.name
    """)
    favorites = cursor.fetchall()
    print(f"\n[OK] Botan's Oshi (Level 5):")
    for name, level, why_like in favorites:
        print(f"    - {name}")
        if why_like:
            print(f"      Reason: {why_like[:80]}...")

    print(f"\n[SUCCESS] Migration verification complete")


def migrate_vtuber_data(db_path='subculture_knowledge.db', json_path='hololive_vtubers.json'):
    """
    Main migration function (unified interface)

    Args:
        db_path: Path to database file
        json_path: Path to JSON knowledge file
    """
    db_path = Path(db_path)
    json_path = Path(json_path)

    # If json_path is relative, look in knowledge directory
    if not json_path.is_absolute():
        # Try relative to this file's directory
        json_path = Path(__file__).parent.parent / 'knowledge' / json_path.name

    # Check if database exists
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Check if JSON exists
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    print(f"[INFO] Starting VTuber data migration...")
    print(f"[INFO] Source: {json_path}")
    print(f"[INFO] Target: {db_path}")

    # Load JSON
    knowledge = load_json_knowledge(str(json_path))

    # Connect to database
    conn = sqlite3.connect(str(db_path))

    try:
        # Migrate master data
        migrate_vtuber_master_data(conn, knowledge)

        # Migrate favorites
        migrate_botan_favorites(conn, knowledge)

        # Set default affinity
        set_default_affinity_levels(conn)

        # Verify
        verify_migration(conn)

        # Update metadata
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE db_metadata
        SET value = ?, updated_at = ?
        WHERE key = 'last_migration'
        """, (datetime.now().isoformat(), datetime.now()))

        cursor.execute("""
        INSERT OR REPLACE INTO db_metadata (key, value, updated_at)
        VALUES ('migration_source', ?, ?)
        """, (str(json_path), datetime.now()))

        conn.commit()

        print(f"\n[SUCCESS] Migration complete!")

    finally:
        conn.close()

    return True


if __name__ == "__main__":
    import sys

    # Paths
    json_path = Path(__file__).parent / 'hololive_vtuber_knowledge.json'
    db_path = Path(__file__).parent / 'subculture_knowledge.db'

    # Check if database exists
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print(f"[INFO] Please run: python create_subculture_db.py")
        sys.exit(1)

    # Check if JSON exists
    if not json_path.exists():
        print(f"[ERROR] JSON file not found: {json_path}")
        sys.exit(1)

    print(f"[INFO] Starting VTuber data migration...")
    print(f"[INFO] Source: {json_path}")
    print(f"[INFO] Target: {db_path}")

    # Load JSON
    knowledge = load_json_knowledge(json_path)

    # Connect to database
    conn = sqlite3.connect(db_path)

    try:
        # Migrate master data
        migrate_vtuber_master_data(conn, knowledge)

        # Migrate favorites
        migrate_botan_favorites(conn, knowledge)

        # Set default affinity
        set_default_affinity_levels(conn)

        # Verify
        verify_migration(conn)

        # Update metadata
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE db_metadata
        SET value = ?, updated_at = ?
        WHERE key = 'last_migration'
        """, (datetime.now().isoformat(), datetime.now()))

        cursor.execute("""
        INSERT OR REPLACE INTO db_metadata (key, value, updated_at)
        VALUES ('migration_source', ?, ?)
        """, (str(json_path), datetime.now()))

        conn.commit()

        print(f"\n[SUCCESS] Migration complete!")
        print(f"\n[NEXT STEPS]")
        print(f"1. Run: python test_subculture_db.py")
        print(f"2. Integrate with chat_with_botan_memories.py")
        print(f"3. Test conversations with VTuber knowledge")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()
