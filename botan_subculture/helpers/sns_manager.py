"""
SNS Manager
===========

Manages VTuber SNS information (Twitter/X accounts and posts)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..config import DB_PATH


class SNSManager:
    """Manages VTuber SNS data"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(self.db_path))

    def get_vtuber_accounts(self, vtuber_name: str) -> List[Dict]:
        """
        Get all SNS accounts for a VTuber

        Args:
            vtuber_name: VTuber's official name

        Returns:
            list: List of account dicts
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT
            a.platform,
            a.account_handle,
            a.account_url,
            a.account_type,
            a.is_verified
        FROM vtuber_sns_accounts a
        JOIN vtubers v ON a.vtuber_id = v.vtuber_id
        WHERE v.name = ?
        ORDER BY
            CASE a.account_type
                WHEN 'main' THEN 1
                WHEN 'sub' THEN 2
                ELSE 3
            END
        """, (vtuber_name,))

        accounts = []
        for platform, handle, url, acc_type, verified in cursor.fetchall():
            accounts.append({
                'platform': platform,
                'handle': handle,
                'url': url,
                'type': acc_type,
                'verified': bool(verified)
            })

        return accounts

    def get_recent_posts(self, vtuber_name: str, days: int = 7, min_importance: int = 3) -> List[Dict]:
        """
        Get recent important posts from a VTuber

        Args:
            vtuber_name: VTuber's official name
            days: Number of days to look back
            min_importance: Minimum importance level (1-5)

        Returns:
            list: List of post dicts
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
        SELECT
            p.post_content,
            p.post_type,
            p.posted_at,
            p.importance_level,
            p.tags,
            p.post_url
        FROM vtuber_sns_posts p
        JOIN vtuber_sns_accounts a ON p.account_id = a.account_id
        JOIN vtubers v ON a.vtuber_id = v.vtuber_id
        WHERE v.name = ?
          AND p.posted_at >= ?
          AND p.importance_level >= ?
        ORDER BY p.posted_at DESC, p.importance_level DESC
        LIMIT 10
        """, (vtuber_name, cutoff_date, min_importance))

        posts = []
        for content, post_type, posted_at, importance, tags, url in cursor.fetchall():
            posts.append({
                'content': content,
                'type': post_type,
                'posted_at': posted_at,
                'importance': importance,
                'tags': tags,
                'url': url
            })

        return posts

    def get_upcoming_activities(self, vtuber_name: str, days_ahead: int = 7) -> List[Dict]:
        """
        Get upcoming activities for a VTuber

        Args:
            vtuber_name: VTuber's official name
            days_ahead: Number of days to look ahead

        Returns:
            list: List of activity dicts
        """
        cursor = self.conn.cursor()

        today = datetime.now().date()
        end_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        cursor.execute("""
        SELECT
            activity_type,
            title,
            description,
            scheduled_date,
            scheduled_time,
            source_url
        FROM vtuber_activities
        WHERE vtuber_id = (SELECT vtuber_id FROM vtubers WHERE name = ?)
          AND scheduled_date >= ?
          AND scheduled_date <= ?
        ORDER BY scheduled_date, scheduled_time
        """, (vtuber_name, today.strftime('%Y-%m-%d'), end_date))

        activities = []
        for act_type, title, desc, date, time, url in cursor.fetchall():
            activities.append({
                'type': act_type,
                'title': title,
                'description': desc,
                'date': date,
                'time': time,
                'url': url
            })

        return activities

    def add_post(self, vtuber_name: str, platform: str, content: str,
                 post_type: str, importance: int = 3, posted_at: str = None,
                 url: str = None, tags: str = None) -> bool:
        """
        Add a post manually

        Args:
            vtuber_name: VTuber's name
            platform: Platform name ('twitter', etc.)
            content: Post content
            post_type: Type ('announcement', 'schedule', 'milestone', 'casual')
            importance: Importance level (1-5)
            posted_at: When posted (YYYY-MM-DD HH:MM:SS format)
            url: Post URL
            tags: Comma-separated tags

        Returns:
            bool: Success
        """
        cursor = self.conn.cursor()

        # Get account_id
        cursor.execute("""
        SELECT a.account_id
        FROM vtuber_sns_accounts a
        JOIN vtubers v ON a.vtuber_id = v.vtuber_id
        WHERE v.name = ? AND a.platform = ? AND a.account_type = 'main'
        """, (vtuber_name, platform))

        result = cursor.fetchone()
        if not result:
            print(f"[ERROR] Account not found: {vtuber_name} on {platform}")
            return False

        account_id = result[0]

        # Insert post
        cursor.execute("""
        INSERT INTO vtuber_sns_posts
        (account_id, platform, post_content, post_type, importance_level, posted_at, post_url, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (account_id, platform, content, post_type, importance, posted_at, url, tags))

        self.conn.commit()
        return True

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
