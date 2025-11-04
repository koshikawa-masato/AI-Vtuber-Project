"""
Update VTuber YouTube Channel IDs
==================================

Updates vtubers table with YouTube channel IDs from hololive_channel_ids.json
"""

import json
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH, KNOWLEDGE_DIR


def load_channel_ids():
    """Load channel IDs from JSON file

    Returns:
        dict: Channel IDs by generation
    """
    channel_ids_file = KNOWLEDGE_DIR / 'hololive_channel_ids.json'

    if not channel_ids_file.exists():
        raise FileNotFoundError(f"Channel IDs file not found: {channel_ids_file}")

    with open(channel_ids_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['channels']


def update_channel_ids(conn, channels_data):
    """Update channel IDs in database

    Args:
        conn: Database connection
        channels_data: Channel data from JSON

    Returns:
        tuple: (updated_count, not_found_count)
    """
    cursor = conn.cursor()

    updated_count = 0
    not_found_count = 0
    not_found_names = []

    # Flatten all channels from all generations
    all_channels = []
    for generation, channels in channels_data.items():
        if generation == 'official':
            continue  # Skip official channel
        all_channels.extend(channels)

    print(f"\nProcessing {len(all_channels)} VTubers...")

    for channel in all_channels:
        name = channel['name']
        channel_id = channel['channel_id']
        handle = channel.get('handle', '')

        # Try to find VTuber by name
        cursor.execute(
            "SELECT vtuber_id, youtube_channel_id FROM vtubers WHERE name = ?",
            (name,)
        )
        result = cursor.fetchone()

        if result:
            vtuber_id, existing_channel_id = result

            if existing_channel_id and existing_channel_id != channel_id:
                print(f"  [WARNING] {name}: Channel ID mismatch")
                print(f"    Existing: {existing_channel_id}")
                print(f"    New:      {channel_id}")

            # Update channel ID and handle
            cursor.execute(
                """
                UPDATE vtubers
                SET youtube_channel_id = ?,
                    twitter_handle = COALESCE(twitter_handle, ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE vtuber_id = ?
                """,
                (channel_id, handle, vtuber_id)
            )

            updated_count += 1
            print(f"  [✓] {name}: Updated channel ID")
        else:
            not_found_count += 1
            not_found_names.append(name)
            print(f"  [✗] {name}: Not found in database")

    conn.commit()

    if not_found_names:
        print(f"\n[WARNING] {not_found_count} VTubers not found in database:")
        for name in not_found_names:
            print(f"  - {name}")
        print("\nThese VTubers need to be added to the database first.")

    return updated_count, not_found_count


def verify_updates(conn):
    """Verify channel IDs were updated

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    # Count VTubers with channel IDs
    cursor.execute(
        "SELECT COUNT(*) FROM vtubers WHERE youtube_channel_id IS NOT NULL"
    )
    with_channel_id = cursor.fetchone()[0]

    # Count total active VTubers
    cursor.execute(
        "SELECT COUNT(*) FROM vtubers WHERE is_active = 1"
    )
    total_active = cursor.fetchone()[0]

    # Get some examples
    cursor.execute(
        """
        SELECT name, youtube_channel_id
        FROM vtubers
        WHERE youtube_channel_id IS NOT NULL
        LIMIT 5
        """
    )
    examples = cursor.fetchall()

    print(f"\n" + "=" * 60)
    print(f"Verification Results")
    print("=" * 60)
    print(f"Active VTubers: {total_active}")
    print(f"With Channel ID: {with_channel_id}")
    print(f"Coverage: {with_channel_id}/{total_active} ({with_channel_id/total_active*100:.1f}%)")

    print(f"\nExamples:")
    for name, channel_id in examples:
        print(f"  {name}: {channel_id}")


def main():
    """Main function"""
    print("=" * 60)
    print("Update VTuber YouTube Channel IDs")
    print("=" * 60)

    try:
        # Load channel IDs
        print("\n[1] Loading channel IDs from JSON...")
        channels_data = load_channel_ids()

        total_channels = sum(
            len(channels)
            for gen, channels in channels_data.items()
            if gen != 'official'
        )
        print(f"    Loaded {total_channels} channel IDs")

        # Connect to database
        print(f"\n[2] Connecting to database: {DB_PATH}")
        if not DB_PATH.exists():
            print(f"    [ERROR] Database not found: {DB_PATH}")
            print("    Please run database creation script first")
            return

        conn = sqlite3.connect(DB_PATH)

        # Update channel IDs
        print("\n[3] Updating channel IDs in database...")
        updated, not_found = update_channel_ids(conn, channels_data)

        # Verify updates
        print("\n[4] Verifying updates...")
        verify_updates(conn)

        conn.close()

        print(f"\n" + "=" * 60)
        print(f"[SUCCESS] Updated {updated} channel IDs")
        if not_found > 0:
            print(f"[INFO] {not_found} VTubers not found (may need to be added first)")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
