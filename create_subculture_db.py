"""
Subculture Knowledge Database Creation Script
==============================================

This script creates the subculture_knowledge.db database
for Botan's "soul" - her dynamic preferences and knowledge.

Distinction from sisters_memory.db:
- sisters_memory.db: Static life experiences (0-17 years, 98 memories)
- subculture_knowledge.db: Dynamic preferences (VTubers, artists, trends)

Usage:
    python create_subculture_db.py

Output:
    subculture_knowledge.db in the same directory
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def create_database(db_path='subculture_knowledge.db'):
    """Create subculture knowledge database with full schema"""

    # Connect to database (creates if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"[INFO] Creating database: {db_path}")

    # ========================================
    # CORE TABLES
    # ========================================

    # VTuber master table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtubers (
        vtuber_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        name_en TEXT,
        agency TEXT,
        generation TEXT,
        debut_date DATE,

        -- Fan information
        fan_name TEXT,
        fan_name_en TEXT,
        fan_individual TEXT,
        fan_mark TEXT,

        -- Character information
        self_title TEXT,
        nickname TEXT,
        greeting TEXT,

        -- Channel information
        youtube_channel_id TEXT UNIQUE,
        twitter_handle TEXT,

        -- Status
        is_active BOOLEAN DEFAULT 1,
        graduation_date DATE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("[OK] Created table: vtubers")

    # Stream records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtuber_streams (
        stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL,

        -- Stream metadata
        stream_date DATE NOT NULL,
        stream_time TIME,
        title TEXT NOT NULL,
        game_name TEXT,
        stream_type TEXT CHECK(stream_type IN ('game', 'singing', 'chatting', 'collab', 'event', 'other')),
        duration_minutes INTEGER,

        -- Content restrictions (IMPORTANT for Hololive guidelines)
        is_member_only BOOLEAN DEFAULT 0,
        is_clip_prohibited BOOLEAN DEFAULT 0,
        content_visibility TEXT CHECK(content_visibility IN ('public', 'member', 'restricted')) DEFAULT 'public',

        -- Stream status (CRITICAL for conversation rules)
        is_ongoing BOOLEAN DEFAULT 0,  -- Still streaming
        stream_end_time TIMESTAMP,     -- When stream ended

        -- Metrics
        viewer_peak INTEGER,
        superchat_amount INTEGER,

        -- Links
        archive_url TEXT UNIQUE,
        youtube_id TEXT UNIQUE,

        -- Metadata
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stream_date ON vtuber_streams(stream_date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vtuber_streams ON vtuber_streams(vtuber_id, stream_date DESC)")
    print("[OK] Created table: vtuber_streams")

    # Catchphrases table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtuber_catchphrases (
        phrase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL,
        phrase TEXT NOT NULL,
        meaning TEXT,
        usage_context TEXT,
        frequency TEXT CHECK(frequency IN ('常用', '時々', '稀')),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
    )
    """)
    print("[OK] Created table: vtuber_catchphrases")

    # Famous episodes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtuber_episodes (
        episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        episode_date DATE,
        description TEXT,
        category TEXT,
        viral_level INTEGER CHECK(viral_level BETWEEN 1 AND 5),

        stream_id INTEGER,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id),
        FOREIGN KEY (stream_id) REFERENCES vtuber_streams(stream_id)
    )
    """)
    print("[OK] Created table: vtuber_episodes")

    # ========================================
    # BOTAN'S PERSONAL TABLES
    # ========================================

    # Botan's affinity levels with VTubers
    # IMPORTANT: Botan watches ALL streams/videos/shorts for ALL members
    # Affinity = preference (how much she likes them), NOT knowledge level
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS botan_vtuber_affinity (
        affinity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL UNIQUE,

        -- Affinity level (1-5) = PREFERENCE, not knowledge
        -- Botan knows EVERYTHING about ALL members
        -- 5: Oshi (favorite) - talks about them enthusiastically
        -- 4: Really likes - mentions them often
        -- 3: Likes - neutral positive
        -- 2: Okay - less enthusiastic
        -- 1: Not particularly interested
        affinity_level INTEGER CHECK(affinity_level BETWEEN 1 AND 5) DEFAULT 3,

        -- Personal preferences
        why_like TEXT,
        favorite_stream_type TEXT,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
    )
    """)
    print("[OK] Created table: botan_vtuber_affinity")

    # Botan's watch history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS botan_watch_history (
        watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id INTEGER,
        vtuber_id INTEGER NOT NULL,

        watched_date DATE NOT NULL,
        watch_type TEXT CHECK(watch_type IN ('live', 'archive', 'clip')),

        -- Botan's reaction
        personal_notes TEXT,
        emotional_reaction TEXT,
        would_recommend BOOLEAN,
        memorable_moment TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (stream_id) REFERENCES vtuber_streams(stream_id),
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_watch_date ON botan_watch_history(watched_date DESC)")
    print("[OK] Created table: botan_watch_history")

    # ========================================
    # EXTENDED SUBCULTURE TABLES (Phase 2+)
    # ========================================

    # Artists table (for Kasho)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_en TEXT,
        category TEXT CHECK(category IN ('musician', 'sound_engineer', 'actor', 'voice_actor', 'other')),
        debut_year INTEGER,

        is_active BOOLEAN DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("[OK] Created table: artists")

    # Light novels table (for Yuri)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS light_novels (
        novel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        category TEXT,
        publication_year INTEGER,

        is_narou BOOLEAN DEFAULT 0,
        narou_url TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("[OK] Created table: light_novels")

    # ========================================
    # METADATA TABLE
    # ========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS db_metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Insert initial metadata
    cursor.execute("""
    INSERT OR REPLACE INTO db_metadata (key, value, updated_at) VALUES
        ('version', '1.0', ?),
        ('created_at', ?, ?),
        ('last_youtube_fetch', NULL, ?),
        ('phase', 'Phase 1: VTuber Knowledge Base', ?)
    """, (datetime.now(), datetime.now(), datetime.now(), datetime.now(), datetime.now()))

    print("[OK] Created table: db_metadata")

    # ========================================
    # COMMIT AND CLOSE
    # ========================================

    conn.commit()
    conn.close()

    print(f"\n[SUCCESS] Database created successfully: {db_path}")
    print(f"[INFO] Total tables: 10")
    print(f"[INFO] Phase 1 tables ready for VTuber data migration")

    return db_path


def verify_database(db_path='subculture_knowledge.db'):
    """Verify database structure"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n[INFO] Verifying database structure...")

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"[OK] Found {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"    - {table_name}: {count} rows")

    conn.close()

    print(f"[SUCCESS] Database verification complete")


if __name__ == "__main__":
    import sys

    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'subculture_knowledge.db'
    db_path = Path(db_path)

    # Check if database already exists
    if db_path.exists():
        print(f"[WARNING] Database already exists: {db_path}")
        response = input("Overwrite? (yes/no): ").strip().lower()
        if response != 'yes':
            print("[CANCELLED] Database creation cancelled")
            sys.exit(0)
        db_path.unlink()
        print(f"[INFO] Deleted existing database")

    # Create database
    created_path = create_database(str(db_path))

    # Verify database
    verify_database(str(db_path))

    print(f"\n[NEXT STEPS]")
    print(f"1. Run: python migrate_vtuber_data.py")
    print(f"2. Run: python test_subculture_db.py")
    print(f"3. Integrate with chat_with_botan_memories.py")
