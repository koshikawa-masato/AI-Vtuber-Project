"""
Database Module CLI
===================

Command-line interface for database operations.

Usage:
    python -m botan_subculture.database create
    python -m botan_subculture.database migrate
    python -m botan_subculture.database verify
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.database.create_db import create_database, verify_database
from botan_subculture.database.migrate_data import migrate_vtuber_data
from botan_subculture.config import DB_PATH


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m botan_subculture.database create   # Create database")
        print("  python -m botan_subculture.database migrate  # Migrate data")
        print("  python -m botan_subculture.database verify   # Verify database")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        create_database(str(DB_PATH))
        verify_database(str(DB_PATH))

    elif command == "migrate":
        migrate_vtuber_data(str(DB_PATH))

    elif command == "verify":
        verify_database(str(DB_PATH))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
