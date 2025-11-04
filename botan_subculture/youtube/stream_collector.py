"""
Stream Metadata Collector
===========================

Collects stream/video metadata from YouTube for all VTubers and saves to database.
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH, YOUTUBE_MAX_RESULTS_PER_REQUEST, YOUTUBE_COLLECTION_LOOKBACK_DAYS
from botan_subculture.youtube import YouTubeClient


class StreamCollector:
    """Collects stream metadata from YouTube"""

    def __init__(self, db_path=None, youtube_client=None):
        """Initialize collector

        Args:
            db_path: Path to database (optional, uses config if not provided)
            youtube_client: YouTube API client (optional, creates new if not provided)
        """
        self.db_path = db_path or DB_PATH
        self.youtube = youtube_client or YouTubeClient()
        self.stats = {
            'processed_channels': 0,
            'new_streams': 0,
            'existing_streams': 0,
            'errors': 0
        }

    def get_vtubers_with_channels(self):
        """Get list of VTubers with YouTube channel IDs

        Returns:
            list: List of (vtuber_id, name, channel_id) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT vtuber_id, name, youtube_channel_id
            FROM vtubers
            WHERE youtube_channel_id IS NOT NULL
              AND is_active = 1
            ORDER BY name
            """
        )
        vtubers = cursor.fetchall()
        conn.close()

        return vtubers

    def get_video_details(self, video_ids):
        """Get detailed information for videos

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            dict: Video details by video ID
        """
        if not video_ids:
            return {}

        try:
            # Get video details (including statistics, contentDetails)
            request = self.youtube.youtube.videos().list(
                part='snippet,contentDetails,statistics,liveStreamingDetails',
                id=','.join(video_ids[:50])  # Max 50 IDs per request
            )
            response = request.execute()

            video_details = {}
            for item in response.get('items', []):
                video_id = item['id']
                video_details[video_id] = item

            return video_details

        except Exception as e:
            print(f"    [ERROR] Failed to get video details: {e}")
            return {}

    def parse_duration(self, duration_str):
        """Parse ISO 8601 duration to minutes

        Args:
            duration_str: ISO 8601 duration string (e.g., 'PT1H30M15S')

        Returns:
            int: Duration in minutes
        """
        if not duration_str:
            return None

        try:
            # Simple parser for PT#H#M#S format
            import re
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 60 + minutes + (1 if seconds > 30 else 0)  # Round seconds
            return None
        except:
            return None

    def classify_stream_type(self, title, description=''):
        """Classify stream type from title and description

        Args:
            title: Video/stream title
            description: Video/stream description

        Returns:
            str: Stream type (game, singing, chatting, collab, event, other)
        """
        title_lower = title.lower()
        desc_lower = description.lower() if description else ''
        combined = title_lower + ' ' + desc_lower

        # Singing
        if any(word in combined for word in ['歌', 'うた', 'sing', 'karaoke', 'カラオケ', '歌枠']):
            return 'singing'

        # Collab
        if any(word in combined for word in ['コラボ', 'collab', 'collaboration', 'with']):
            return 'collab'

        # Event
        if any(word in combined for word in ['イベント', 'event', '記念', '周年', 'anniversary', 'birthday', '誕生日']):
            return 'event'

        # Chatting
        if any(word in combined for word in ['雑談', 'chat', 'talk', 'おしゃべり', 'お話']):
            return 'chatting'

        # Game (default if no other match)
        return 'game'

    def check_content_restrictions(self, title, description=''):
        """Check for content restrictions from title/description

        Args:
            title: Video/stream title
            description: Video/stream description

        Returns:
            tuple: (is_member_only, is_clip_prohibited, visibility)
        """
        title_lower = title.lower()

        # Only check title for member-only markers (description often has "become a member" etc.)
        is_member_only = any(word in title_lower for word in [
            'メン限', 'メンバー限定', 'メンバーシップ限定',
            'members only', 'membership only'
        ])

        # Check both title and description for clip restrictions
        combined = (title + ' ' + (description or '')).lower()
        is_clip_prohibited = any(word in combined for word in [
            '切り抜き禁止', 'no clip', '転載禁止', 'no reupload'
        ])

        if is_member_only:
            visibility = 'member'
        elif is_clip_prohibited:
            visibility = 'restricted'
        else:
            visibility = 'public'

        return is_member_only, is_clip_prohibited, visibility

    def save_stream_metadata(self, vtuber_id, video_data):
        """Save stream metadata to database

        Args:
            vtuber_id: VTuber ID in database
            video_data: Video data from YouTube API

        Returns:
            bool: True if saved, False if already exists
        """
        try:
            snippet = video_data.get('snippet', {})
            content_details = video_data.get('contentDetails', {})
            statistics = video_data.get('statistics', {})
            live_details = video_data.get('liveStreamingDetails', {})

            youtube_id = video_data['id']
            title = snippet.get('title', 'Untitled')
            description = snippet.get('description', '')
            published_at = snippet.get('publishedAt', '')

            # Parse publish date/time
            if published_at:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                stream_date = dt.date().isoformat()  # Convert to string
                stream_time = dt.time().isoformat()  # Convert to string
            else:
                stream_date = datetime.now().date().isoformat()
                stream_time = None

            # Parse duration
            duration_str = content_details.get('duration', '')
            duration_minutes = self.parse_duration(duration_str)

            # Classify stream type
            stream_type = self.classify_stream_type(title, description)

            # Check content restrictions
            is_member_only, is_clip_prohibited, visibility = self.check_content_restrictions(title, description)

            # Check if ongoing (live)
            is_ongoing = live_details.get('actualStartTime') and not live_details.get('actualEndTime')

            # Get stream end time
            stream_end_time = None
            if live_details.get('actualEndTime'):
                stream_end_time = live_details['actualEndTime']

            # Get statistics
            viewer_peak = int(live_details.get('concurrentViewers', 0) or statistics.get('viewCount', 0) or 0)

            # Build archive URL
            archive_url = f"https://www.youtube.com/watch?v={youtube_id}"

            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if already exists
            cursor.execute("SELECT stream_id FROM vtuber_streams WHERE youtube_id = ?", (youtube_id,))
            if cursor.fetchone():
                conn.close()
                return False  # Already exists

            # Insert new stream
            cursor.execute(
                """
                INSERT INTO vtuber_streams (
                    vtuber_id, stream_date, stream_time, title,
                    stream_type, duration_minutes,
                    is_member_only, is_clip_prohibited, content_visibility,
                    is_ongoing, stream_end_time,
                    viewer_peak, archive_url, youtube_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vtuber_id, stream_date, stream_time, title,
                    stream_type, duration_minutes,
                    is_member_only, is_clip_prohibited, visibility,
                    is_ongoing, stream_end_time,
                    viewer_peak, archive_url, youtube_id
                )
            )

            conn.commit()
            conn.close()
            return True  # Newly saved

        except Exception as e:
            print(f"    [ERROR] Failed to save metadata: {e}")
            return False

    def collect_for_vtuber(self, vtuber_id, name, channel_id, max_results=10):
        """Collect stream metadata for a single VTuber

        Args:
            vtuber_id: VTuber ID in database
            name: VTuber name
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to collect

        Returns:
            int: Number of new streams collected
        """
        print(f"\n[{name}]")
        print(f"  Channel ID: {channel_id}")

        try:
            # Get recent uploads
            uploads = self.youtube.get_channel_uploads(channel_id, max_results=max_results)

            if not uploads:
                print(f"  No recent uploads found")
                return 0

            # Extract video IDs
            video_ids = [item['contentDetails']['videoId'] for item in uploads]

            # Get detailed video information
            video_details = self.get_video_details(video_ids)

            # Save each video
            new_count = 0
            for video_id in video_ids:
                video_data = video_details.get(video_id)
                if video_data:
                    is_new = self.save_stream_metadata(vtuber_id, video_data)
                    if is_new:
                        new_count += 1
                        title = video_data['snippet']['title']
                        print(f"  [✓ NEW] {title[:60]}")
                    else:
                        self.stats['existing_streams'] += 1
                else:
                    print(f"  [✗] Failed to get details for video {video_id}")

            print(f"  Summary: {new_count} new, {len(video_ids) - new_count} existing")
            return new_count

        except Exception as e:
            print(f"  [ERROR] {e}")
            self.stats['errors'] += 1
            return 0

    def collect_all(self, max_results_per_channel=10, rate_limit_delay=1.0):
        """Collect stream metadata for all VTubers

        Args:
            max_results_per_channel: Max videos to collect per channel
            rate_limit_delay: Delay between API calls (seconds)

        Returns:
            dict: Collection statistics
        """
        vtubers = self.get_vtubers_with_channels()

        print(f"\n" + "=" * 60)
        print(f"Collecting stream metadata for {len(vtubers)} VTubers")
        print("=" * 60)

        for vtuber_id, name, channel_id in vtubers:
            self.stats['processed_channels'] += 1

            new_count = self.collect_for_vtuber(vtuber_id, name, channel_id, max_results=max_results_per_channel)
            self.stats['new_streams'] += new_count

            # Rate limiting
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        return self.stats

    def print_summary(self):
        """Print collection summary"""
        print(f"\n" + "=" * 60)
        print(f"Collection Summary")
        print("=" * 60)
        print(f"Channels processed: {self.stats['processed_channels']}")
        print(f"New streams collected: {self.stats['new_streams']}")
        print(f"Existing streams skipped: {self.stats['existing_streams']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main function"""
    print("=" * 60)
    print("Stream Metadata Collector")
    print("=" * 60)

    try:
        collector = StreamCollector()

        # Collect metadata for all VTubers
        stats = collector.collect_all(max_results_per_channel=5, rate_limit_delay=0.5)

        # Print summary
        collector.print_summary()

        if stats['new_streams'] > 0:
            print(f"\n[SUCCESS] Collected {stats['new_streams']} new streams!")
        else:
            print(f"\n[INFO] No new streams found (all up to date)")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
