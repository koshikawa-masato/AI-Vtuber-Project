"""
YouTube Data API v3 Client
===========================

Basic client for interacting with YouTube Data API v3.
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import (
    YOUTUBE_API_KEY,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION
)


class YouTubeClient:
    """Client for YouTube Data API v3"""

    def __init__(self, api_key=None):
        """Initialize YouTube API client

        Args:
            api_key: YouTube Data API v3 key (optional, uses env var if not provided)
        """
        self.api_key = api_key or YOUTUBE_API_KEY

        if not self.api_key or self.api_key == 'YOUR_API_KEY_HERE':
            raise ValueError(
                "YouTube API key not set. Please set YOUTUBE_API_KEY in .env file"
            )

        self.youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=self.api_key
        )

    def test_connection(self):
        """Test API connection by fetching a channel

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test with Hololive Official channel
            request = self.youtube.channels().list(
                part='snippet',
                id='UCJFZiqLMntJufDCHc6bQixg'  # Hololive Official
            )
            response = request.execute()

            if response.get('items'):
                channel = response['items'][0]
                print(f"[SUCCESS] Connected to YouTube API")
                print(f"Test channel: {channel['snippet']['title']}")
                return True
            else:
                print("[ERROR] No channel found")
                return False

        except HttpError as e:
            print(f"[ERROR] HTTP Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return False

    def get_channel_info(self, channel_id):
        """Get channel information

        Args:
            channel_id: YouTube channel ID

        Returns:
            dict: Channel information or None if error
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=channel_id
            )
            response = request.execute()

            if response.get('items'):
                return response['items'][0]
            else:
                return None

        except HttpError as e:
            print(f"[ERROR] Failed to get channel info: {e}")
            return None

    def get_channel_uploads(self, channel_id, max_results=10):
        """Get recent uploads from a channel

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of results to return

        Returns:
            list: List of video information or None if error
        """
        try:
            # Get uploads playlist ID
            channel = self.get_channel_info(channel_id)
            if not channel:
                return None

            uploads_playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']

            # Get videos from uploads playlist
            request = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            response = request.execute()

            return response.get('items', [])

        except HttpError as e:
            print(f"[ERROR] Failed to get channel uploads: {e}")
            return None


def main():
    """Test YouTube API connection"""
    print("=" * 60)
    print("YouTube Data API v3 Connection Test")
    print("=" * 60)

    try:
        client = YouTubeClient()

        # Test connection
        print("\n[1] Testing API connection...")
        if client.test_connection():
            print("\n[SUCCESS] YouTube API is working!")

            # Get Sakura Miko's channel as test
            print("\n[2] Testing channel info retrieval...")
            print("    Fetching Sakura Miko's channel...")
            miko_channel_id = 'UC-hM6YJuNYVAmUWxeIr9FeA'
            channel = client.get_channel_info(miko_channel_id)

            if channel:
                snippet = channel['snippet']
                stats = channel['statistics']
                print(f"    Channel: {snippet['title']}")
                print(f"    Subscribers: {stats.get('subscriberCount', 'N/A')}")
                print(f"    Total Views: {stats.get('viewCount', 'N/A')}")
                print(f"    Total Videos: {stats.get('videoCount', 'N/A')}")

                # Get recent uploads
                print("\n[3] Testing recent uploads retrieval...")
                uploads = client.get_channel_uploads(miko_channel_id, max_results=5)

                if uploads:
                    print(f"    Found {len(uploads)} recent videos:")
                    for idx, item in enumerate(uploads, 1):
                        video_title = item['snippet']['title']
                        published = item['snippet']['publishedAt']
                        print(f"    {idx}. {video_title}")
                        print(f"       Published: {published}")

                    print("\n" + "=" * 60)
                    print("[SUCCESS] All tests passed!")
                    print("=" * 60)
                else:
                    print("[WARNING] No recent uploads found")
            else:
                print("[ERROR] Failed to get channel info")
        else:
            print("\n[FAILED] API connection test failed")
            print("Please check your API key in .env file")

    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("\nPlease edit .env file and set your YouTube API key:")
        print("  YOUTUBE_API_KEY=your_actual_api_key_here")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")


if __name__ == '__main__':
    main()
