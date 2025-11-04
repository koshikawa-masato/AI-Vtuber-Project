#!/usr/bin/env python3
"""
Copy Robot Creation Script
Creates a 100% copy of sisters_memory.db for safe testing

Usage:
    python3 scripts/create_copy_robot.py

Output:
    copy_robots/COPY_ROBOT_YYYYMMDD_HHMMSS.db
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def create_copy_robot():
    """Create copy robot from original sisters_memory.db"""

    # Paths
    base_dir = Path("/home/koshikawa/toExecUnit")
    original_db = base_dir / "sisters_memory.db"
    copy_robots_dir = base_dir / "copy_robots"

    # Create copy_robots directory if not exists
    copy_robots_dir.mkdir(exist_ok=True)

    # Check original DB exists
    if not original_db.exists():
        print(f"[ERROR] Original DB not found: {original_db}")
        return None

    # Generate copy robot name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    copy_robot_name = f"COPY_ROBOT_{timestamp}.db"
    copy_robot_path = copy_robots_dir / copy_robot_name

    print(f"\n{'='*60}")
    print(f"Copy Robot Creation")
    print(f"{'='*60}")
    print(f"Original: {original_db}")
    print(f"Copy Robot: {copy_robot_path}")

    # Get original DB size
    original_size = original_db.stat().st_size
    print(f"Original Size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")

    # Copy DB file
    print(f"\nCopying database...")
    try:
        shutil.copy2(original_db, copy_robot_path)
        print(f"[OK] Copy completed")
    except Exception as e:
        print(f"[ERROR] Copy failed: {e}")
        return None

    # Verify copy
    copy_size = copy_robot_path.stat().st_size
    print(f"Copy Size: {copy_size:,} bytes ({copy_size/1024/1024:.2f} MB)")

    if original_size != copy_size:
        print(f"[WARNING] Size mismatch!")
        return None

    # Get statistics from copy robot
    print(f"\n{'='*60}")
    print(f"Copy Robot Statistics")
    print(f"{'='*60}")

    try:
        conn = sqlite3.connect(copy_robot_path)
        cursor = conn.cursor()

        # Event count
        cursor.execute("SELECT COUNT(*) FROM sister_shared_events")
        event_count = cursor.fetchone()[0]
        print(f"Events: {event_count}")

        # Memory count (per sister)
        for sister in ["botan", "kasho", "yuri"]:
            cursor.execute(f"SELECT COUNT(*) FROM {sister}_memory")
            memory_count = cursor.fetchone()[0]
            print(f"{sister.capitalize()} Memories: {memory_count}")

        # Inspiration count
        cursor.execute("SELECT COUNT(*) FROM sister_shared_inspirations")
        inspiration_count = cursor.fetchone()[0]
        print(f"Inspirations: {inspiration_count}")

        conn.close()

    except Exception as e:
        print(f"[WARNING] Could not get statistics: {e}")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Copy Robot Created")
    print(f"{'='*60}")
    print(f"Path: {copy_robot_path}")
    print(f"Name: {copy_robot_name}")
    print(f"\nIMPORTANT: This copy robot's memory will NEVER be fed back to original DB.")
    print(f"{'='*60}\n")

    return copy_robot_path


if __name__ == "__main__":
    copy_robot_path = create_copy_robot()

    if copy_robot_path:
        print(f"\nNext steps:")
        print(f"1. python3 scripts/snapshot_before_education.py --db {copy_robot_path.name}")
        print(f"2. python3 scripts/train_sensitive_judgment.py --db {copy_robot_path.name}")
        print(f"3. python3 scripts/snapshot_after_education.py --db {copy_robot_path.name}")
        print(f"4. python3 scripts/compare_education_results.py")
