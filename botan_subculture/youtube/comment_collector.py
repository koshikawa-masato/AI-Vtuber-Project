"""
YouTube Comment Collector
==========================

Collects comments from YouTube videos to understand stream content.
"""

import sqlite3
import sys
from pathlib import Path
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH
from botan_subculture.youtube import YouTubeClient


class CommentCollector:
    """Collects comments from YouTube videos"""

    def __init__(self, db_path=None, youtube_client=None):
        """Initialize collector

        Args:
            db_path: Path to database
            youtube_client: YouTube API client
        """
        self.db_path = db_path or DB_PATH
        self.youtube = youtube_client or YouTubeClient()
        self.stats = {
            'processed_streams': 0,
            'new_comments': 0,
            'errors': 0
        }

    def get_stream_comments(self, video_id, max_results=100):
        """Get comments from a YouTube video

        Args:
            video_id: YouTube video ID
            max_results: Maximum comments to retrieve

        Returns:
            list: List of comment data
        """
        try:
            # Get comment threads (top-level comments + replies)
            request = self.youtube.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                order='relevance',  # Get most relevant/liked comments
                textFormat='plainText'
            )
            response = request.execute()

            comments = []
            for item in response.get('items', []):
                snippet = item['snippet']
                top_comment = snippet['topLevelComment']['snippet']

                comment_data = {
                    'youtube_comment_id': item['id'],
                    'author_name': top_comment.get('authorDisplayName', ''),
                    'author_channel_id': top_comment.get('authorChannelId', {}).get('value', ''),
                    'text_display': top_comment.get('textDisplay', ''),
                    'text_original': top_comment.get('textOriginal', ''),
                    'like_count': top_comment.get('likeCount', 0),
                    'published_at': top_comment.get('publishedAt', ''),
                    'updated_at': top_comment.get('updatedAt', ''),
                    'reply_count': snippet.get('totalReplyCount', 0)
                }

                comments.append(comment_data)

            return comments

        except Exception as e:
            print(f"    [ERROR] Failed to get comments: {e}")
            return []

    def save_comments(self, stream_id, comments):
        """Save comments to database

        Args:
            stream_id: Stream ID in database
            comments: List of comment data

        Returns:
            int: Number of new comments saved
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for comment in comments:
            try:
                # Check if comment already exists
                cursor.execute(
                    "SELECT comment_id FROM stream_comments WHERE youtube_comment_id = ?",
                    (comment['youtube_comment_id'],)
                )
                if cursor.fetchone():
                    continue  # Already exists

                # Insert comment
                cursor.execute("""
                INSERT INTO stream_comments (
                    stream_id,
                    youtube_comment_id,
                    author_name,
                    author_channel_id,
                    text_display,
                    text_original,
                    like_count,
                    reply_count,
                    published_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stream_id,
                    comment['youtube_comment_id'],
                    comment['author_name'],
                    comment['author_channel_id'],
                    comment['text_display'],
                    comment['text_original'],
                    comment['like_count'],
                    comment['reply_count'],
                    comment['published_at'],
                    comment['updated_at']
                ))

                saved_count += 1

            except Exception as e:
                print(f"    [ERROR] Failed to save comment: {e}")

        conn.commit()
        conn.close()

        return saved_count

    def collect_for_stream(self, stream_id, youtube_id, title, max_comments=100):
        """Collect comments for a single stream

        Args:
            stream_id: Stream ID in database
            youtube_id: YouTube video ID
            title: Stream title
            max_comments: Maximum comments to collect

        Returns:
            int: Number of new comments collected
        """
        print(f"\n[Stream {stream_id}]")
        print(f"  Title: {title[:60]}...")
        print(f"  Video ID: {youtube_id}")

        # Get comments
        comments = self.get_stream_comments(youtube_id, max_results=max_comments)

        if not comments:
            print(f"  No comments found (or comments disabled)")
            return 0

        # Save comments
        saved = self.save_comments(stream_id, comments)

        print(f"  Comments: {saved} new, {len(comments) - saved} existing")

        return saved

    def collect_all_missing(self, max_comments_per_stream=100, rate_limit_delay=1.0):
        """Collect comments for all streams that don't have comments yet

        Args:
            max_comments_per_stream: Max comments to collect per stream
            rate_limit_delay: Delay between API calls (seconds)

        Returns:
            dict: Collection statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get streams without comments (from last 7 days)
        cursor.execute("""
        SELECT
            s.stream_id,
            s.youtube_id,
            s.title,
            v.name
        FROM vtuber_streams s
        JOIN vtubers v ON s.vtuber_id = v.vtuber_id
        WHERE s.youtube_id IS NOT NULL
        AND s.stream_date >= date('now', '-7 days')
        AND NOT EXISTS (
            SELECT 1 FROM stream_comments c
            WHERE c.stream_id = s.stream_id
        )
        ORDER BY s.stream_date DESC
        """)

        streams = cursor.fetchall()
        conn.close()

        print(f"\n" + "=" * 60)
        print(f"Collecting comments for {len(streams)} streams")
        print("=" * 60)

        for stream_id, youtube_id, title, vtuber_name in streams:
            self.stats['processed_streams'] += 1

            print(f"\n[{vtuber_name}]")
            new_count = self.collect_for_stream(stream_id, youtube_id, title, max_comments_per_stream)
            self.stats['new_comments'] += new_count

            # Rate limiting
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        return self.stats

    def print_summary(self):
        """Print collection summary"""
        print(f"\n" + "=" * 60)
        print(f"Comment Collection Summary")
        print("=" * 60)
        print(f"Streams processed: {self.stats['processed_streams']}")
        print(f"New comments collected: {self.stats['new_comments']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main function"""
    print("=" * 60)
    print("YouTube Comment Collector")
    print("=" * 60)

    try:
        collector = CommentCollector()

        # Collect comments for all streams without comments
        stats = collector.collect_all_missing(
            max_comments_per_stream=50,
            rate_limit_delay=0.5
        )

        # Print summary
        collector.print_summary()

        if stats['new_comments'] > 0:
            print(f"\n[SUCCESS] Collected {stats['new_comments']} comments!")
        else:
            print(f"\n[INFO] No new comments (all up to date)")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
