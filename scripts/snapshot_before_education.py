#!/usr/bin/env python3
"""
Educational Snapshot (Before) Script
Captures copy robot state before sensitive judgment training

Usage:
    python3 scripts/snapshot_before_education.py --db COPY_ROBOT_YYYYMMDD_HHMMSS.db

Output:
    snapshots/before_YYYYMMDD_HHMMSS.json
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def get_database_statistics(db_path):
    """Get comprehensive statistics from copy robot database"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {}

    try:
        # Event statistics
        cursor.execute("SELECT COUNT(*) FROM sister_shared_events")
        stats["event_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
        stats["latest_event_id"] = cursor.fetchone()[0]

        # Memory statistics (per sister)
        stats["memory_per_sister"] = {}
        for sister in ["botan", "kasho", "yuri"]:
            cursor.execute(f"SELECT COUNT(*) FROM {sister}_memories")
            memory_count = cursor.fetchone()[0]
            stats["memory_per_sister"][sister] = memory_count

            # Average importance
            cursor.execute(f"SELECT AVG(memory_importance) FROM {sister}_memories")
            avg_importance = cursor.fetchone()[0]
            stats["memory_per_sister"][f"{sister}_avg_importance"] = (
                round(avg_importance, 4) if avg_importance else 0.0
            )

        # Inspiration statistics (if table exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM sister_shared_inspirations")
            stats["inspiration_count"] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats["inspiration_count"] = 0

        # Relationship parameters (if exists)
        try:
            cursor.execute("SELECT trust, affection, respect, dependence FROM relationship_parameters LIMIT 1")
            row = cursor.fetchone()
            if row:
                stats["relationship_params"] = {
                    "trust": row[0],
                    "affection": row[1],
                    "respect": row[2],
                    "dependence": row[3]
                }
            else:
                stats["relationship_params"] = None
        except sqlite3.OperationalError:
            stats["relationship_params"] = None

    except Exception as e:
        print(f"[WARNING] Error getting statistics: {e}")
        raise

    finally:
        conn.close()

    return stats


def create_before_snapshot(db_name):
    """Create snapshot before education"""

    # Paths
    base_dir = Path("/home/koshikawa/toExecUnit")
    db_path = base_dir / "copy_robots" / db_name
    snapshots_dir = base_dir / "snapshots"

    # Create snapshots directory
    snapshots_dir.mkdir(exist_ok=True)

    # Check DB exists
    if not db_path.exists():
        print(f"[ERROR] Copy robot DB not found: {db_path}")
        return None

    # Generate snapshot name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"before_{timestamp}.json"
    snapshot_path = snapshots_dir / snapshot_name

    print(f"\n{'='*60}")
    print(f"Educational Snapshot (Before)")
    print(f"{'='*60}")
    print(f"Copy Robot: {db_name}")
    print(f"Snapshot: {snapshot_name}")

    # Get database statistics
    print(f"\nCollecting statistics...")
    try:
        stats = get_database_statistics(db_path)
    except Exception as e:
        print(f"[ERROR] Failed to collect statistics: {e}")
        return None

    # Create snapshot data
    snapshot_data = {
        "snapshot_id": f"before_{timestamp}",
        "snapshot_type": "before_education",
        "timestamp": datetime.now().isoformat(),
        "copy_robot_db": db_name,
        "statistics": stats,
        "learning_status": {
            "categories_learned": [],
            "total_examples_processed": 0,
            "learning_completed": False
        }
    }

    # Save snapshot
    print(f"\nSaving snapshot...")
    try:
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Snapshot saved")
    except Exception as e:
        print(f"[ERROR] Failed to save snapshot: {e}")
        return None

    # Display summary
    print(f"\n{'='*60}")
    print(f"Snapshot Summary")
    print(f"{'='*60}")
    print(f"Events: {stats['event_count']} (latest: #{stats['latest_event_id']})")
    print(f"Memories:")
    for sister in ["botan", "kasho", "yuri"]:
        count = stats["memory_per_sister"][sister]
        avg_imp = stats["memory_per_sister"][f"{sister}_avg_importance"]
        print(f"  {sister.capitalize()}: {count} (avg importance: {avg_imp:.4f})")
    print(f"Inspirations: {stats['inspiration_count']}")

    if stats["relationship_params"]:
        print(f"Relationship Parameters:")
        for key, value in stats["relationship_params"].items():
            print(f"  {key.capitalize()}: {value:.4f}")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Before-Education Snapshot Created")
    print(f"{'='*60}")
    print(f"Path: {snapshot_path}")
    print(f"\n{'='*60}\n")

    return snapshot_path, timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create before-education snapshot")
    parser.add_argument("--db", required=True, help="Copy robot DB name (e.g., COPY_ROBOT_20251029_150000.db)")
    args = parser.parse_args()

    result = create_before_snapshot(args.db)

    if result:
        snapshot_path, timestamp = result
        print(f"Next step:")
        print(f"python3 scripts/train_sensitive_judgment.py --db {args.db} --before-snapshot {timestamp}")
