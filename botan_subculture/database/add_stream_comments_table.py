"""
Add stream_comments table to database
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH


def add_stream_comments_table():
    """Add stream_comments table to existing database"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create stream_comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stream_comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id INTEGER NOT NULL,

        -- Comment metadata
        youtube_comment_id TEXT UNIQUE,
        author_name TEXT,
        author_channel_id TEXT,

        -- Comment content
        text_display TEXT,
        text_original TEXT,

        -- Engagement
        like_count INTEGER DEFAULT 0,
        reply_count INTEGER DEFAULT 0,

        -- Timing
        published_at TIMESTAMP,
        updated_at TIMESTAMP,

        -- Parent comment (for replies)
        parent_id INTEGER,

        -- Collection metadata
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (stream_id) REFERENCES vtuber_streams(stream_id),
        FOREIGN KEY (parent_id) REFERENCES stream_comments(comment_id)
    )
    """)

    # Create index for faster lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_stream_comments_stream_id
    ON stream_comments(stream_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_stream_comments_like_count
    ON stream_comments(like_count DESC)
    """)

    conn.commit()
    conn.close()

    print("[SUCCESS] stream_comments table created")


if __name__ == '__main__':
    add_stream_comments_table()
