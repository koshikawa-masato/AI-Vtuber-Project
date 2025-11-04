"""
Conversation Context Builder
============================

Builds safe conversation context for Botan to talk about VTubers.

Key Features:
- Retrieves recent streams (public only)
- Gets VTuber affinity level
- Formats context for LLM prompt
- Ensures content restriction compliance
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .content_restriction import ContentRestrictionChecker
from .knowledge_manager import KnowledgeManager
from .sns_manager import SNSManager
from ..config import DB_PATH, DEFAULT_LOOKBACK_DAYS, MAX_RECENT_STREAMS


class ConversationContextBuilder:
    """Build conversation context for Botan's chat"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.conn = sqlite3.connect(str(self.db_path))
        self.restriction_checker = ContentRestrictionChecker(str(self.db_path))
        self.knowledge = KnowledgeManager(self.db_path)
        self.sns = SNSManager(self.db_path)

    def get_vtuber_info(self, vtuber_name: str) -> Optional[Dict]:
        """
        Get basic VTuber information

        Args:
            vtuber_name: VTuber's name

        Returns:
            dict: {
                'vtuber_id': int,
                'name': str,
                'fan_name': str,
                'self_title': str,
                'affinity_level': int,
                'why_like': str
            }
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT
            v.vtuber_id,
            v.name,
            v.fan_name,
            v.self_title,
            a.affinity_level,
            a.why_like
        FROM vtubers v
        LEFT JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
        WHERE v.name = ?
        """, (vtuber_name,))

        result = cursor.fetchone()
        if not result:
            return None

        return {
            'vtuber_id': result[0],
            'name': result[1],
            'fan_name': result[2],
            'self_title': result[3],
            'affinity_level': result[4] or 3,  # Default affinity
            'why_like': result[5]
        }

    def get_stream_highlights(self, stream_id: int, max_comments: int = 3) -> List[Dict]:
        """
        Get top comments from a stream (sorted by likes)

        Args:
            stream_id: Stream ID in database
            max_comments: Maximum number of comments to return

        Returns:
            list: List of comment dicts with author, text, likes
        """
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT author_name, text_original, like_count
        FROM stream_comments
        WHERE stream_id = ?
        ORDER BY like_count DESC
        LIMIT ?
        """, (stream_id, max_comments))

        highlights = []
        for author, text, likes in cursor.fetchall():
            # Truncate long comments (increased limit for better context)
            text_preview = text[:300] + '...' if len(text) > 300 else text
            highlights.append({
                'author': author,
                'text': text_preview,
                'likes': likes
            })

        return highlights

    def get_recent_streams_context(
        self,
        vtuber_name: str,
        days: int = DEFAULT_LOOKBACK_DAYS,
        limit: int = MAX_RECENT_STREAMS
    ) -> Dict:
        """
        Get recent streams context for conversation

        Args:
            vtuber_name: VTuber's name
            days: Number of days to look back
            limit: Maximum number of streams to return

        Returns:
            dict: {
                'vtuber_info': dict,
                'recent_streams': list of dicts,
                'total_watched': int,
                'can_mention': int
            }
        """
        vtuber_info = self.get_vtuber_info(vtuber_name)
        if not vtuber_info:
            return None

        vtuber_id = vtuber_info['vtuber_id']

        # Get all recent streams (Botan watched ALL of them)
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
        SELECT COUNT(*)
        FROM vtuber_streams
        WHERE vtuber_id = ?
          AND stream_date >= ?
        """, (vtuber_id, cutoff_date))

        total_watched = cursor.fetchone()[0]

        # Get mentionable streams (public, not ongoing)
        mentionable = self.restriction_checker.get_mentionable_streams(
            vtuber_id, days
        )

        recent_streams = []
        for stream_id, name, title, stream_date in mentionable[:limit]:
            # Get highlights (top comments) for this stream
            highlights = self.get_stream_highlights(stream_id, max_comments=3)

            recent_streams.append({
                'stream_id': stream_id,
                'title': title,
                'date': stream_date,
                'highlights': highlights
            })

        return {
            'vtuber_info': vtuber_info,
            'recent_streams': recent_streams,
            'total_watched': total_watched,
            'can_mention': len(mentionable),
            'watched_all': True  # Botan ALWAYS watches everything
        }

    def build_system_prompt_addition(self, context: Dict) -> str:
        """
        Build additional system prompt based on context

        Args:
            context: Context from get_recent_streams_context()

        Returns:
            str: Additional system prompt
        """
        if not context:
            return ""

        vtuber_info = context['vtuber_info']
        affinity = vtuber_info['affinity_level']

        # Affinity-based tone
        if affinity == 5:
            tone = "enthusiastically and in detail"
        elif affinity >= 3:
            tone = "in a friendly, positive way"
        else:
            tone = "briefly but knowledgeably"

        # Calculate days ago for each stream
        from datetime import datetime, date, timedelta
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')

        prompt = f"""
[IMPORTANT: TODAY'S DATE]
Today is {today_str} ({today.strftime('%Y年%m月%d日')})

[Current Topic: {vtuber_info['name']}]

VTuber Info:
- Name: {vtuber_info['name']}
- Fan Name: {vtuber_info['fan_name'] or 'N/A'}
- Self Title: {vtuber_info['self_title'] or 'N/A'}
- Your Affinity: Level {affinity}/5

Recent Streams (last {DEFAULT_LOOKBACK_DAYS} days):
- Total watched: {context['total_watched']} streams (you watched ALL of them)
- Can mention: {context['can_mention']} streams (public, ended)

"""

        if context['recent_streams']:
            prompt += "Recent mentionable streams (with ACCURATE dates):\n"
            for stream in context['recent_streams'][:5]:
                stream_date = datetime.strptime(stream['date'], '%Y-%m-%d').date()
                days_ago = (today - stream_date).days

                if days_ago == 0:
                    date_label = "TODAY (今日)"
                elif days_ago == 1:
                    date_label = "YESTERDAY (昨日)"
                elif days_ago == 2:
                    date_label = "2 days ago (一昨日)"
                else:
                    date_label = f"{days_ago} days ago ({days_ago}日前)"

                prompt += f"  - [{stream['date']}] = {date_label}\n"
                prompt += f"    Title: {stream['title']}\n"

                # Add stream highlights from comments (if available)
                if stream.get('highlights'):
                    prompt += f"    Stream Owner: {vtuber_info['name']} (配信主 - ALWAYS a participant!)\n"
                    prompt += f"    Stream Highlights (from viewer comments):\n"
                    for highlight in stream['highlights'][:3]:  # Top 3 comments
                        prompt += f"      • {highlight['text']} ({highlight['likes']} likes)\n"

        prompt += f"\n[CRITICAL: TIME AWARENESS]\n"
        prompt += f"- ALWAYS check the date carefully when answering questions\n"
        prompt += f"- If user asks about 'yesterday (昨日)', talk ONLY about {(today - timedelta(days=1)).strftime('%Y-%m-%d')} streams\n"
        prompt += f"- If user asks about 'today (今日)', talk ONLY about {today_str} streams\n"
        prompt += f"- DO NOT mix up dates or confuse different days' streams\n"
        prompt += f"- When mentioning a stream, ALWAYS reference the exact date\n"

        prompt += f"\nTalk about {vtuber_info['name']} {tone}.\n"

        if affinity == 5:
            prompt += f"You LOVE {vtuber_info['name']}! Show your enthusiasm!\n"
            if vtuber_info['why_like']:
                prompt += f"Why you like: {vtuber_info['why_like']}\n"

        return prompt

    def get_all_favorites(self) -> List[Dict]:
        """
        Get all VTubers with affinity level 5 (favorites)

        Returns:
            list: List of favorite VTubers with info
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT
            v.name,
            v.fan_name,
            v.self_title,
            a.why_like
        FROM vtubers v
        JOIN botan_vtuber_affinity a ON v.vtuber_id = a.vtuber_id
        WHERE a.affinity_level = 5
        ORDER BY v.name
        """)

        favorites = []
        for row in cursor.fetchall():
            favorites.append({
                'name': row[0],
                'fan_name': row[1],
                'self_title': row[2],
                'why_like': row[3]
            })

        return favorites

    def get_unit_context(self, message: str) -> str:
        """
        Get unit information context if unit name is mentioned

        Args:
            message: User's message

        Returns:
            str: Additional context about units
        """
        context = ""

        # Get all known units
        all_units = self.knowledge.get_all_units()

        # Check if any unit is mentioned
        mentioned_units = []
        for unit_name in all_units:
            if unit_name in message:
                mentioned_units.append(unit_name)

        # Add unit information to context
        for unit_name in mentioned_units:
            unit_info = self.knowledge.get_unit_info(unit_name)
            if unit_info:
                context += f"\n[UNIT KNOWLEDGE - {unit_name}]\n"
                context += f"Members: {', '.join(unit_info['members'])}\n"
                context += f"Description: {unit_info['description']}\n"
                context += f"Official Unit: {'Yes' if unit_info['official'] else 'No'}\n"
                context += f"CRITICAL: This is VERIFIED information. Use these exact names.\n"

        return context

    def get_sns_context(self, vtuber_name: str) -> str:
        """
        Get SNS information (recent posts, accounts) for a VTuber

        Args:
            vtuber_name: VTuber's name

        Returns:
            str: SNS context
        """
        context = ""

        # Get Twitter/X account
        accounts = self.sns.get_vtuber_accounts(vtuber_name)
        if accounts:
            main_account = next((a for a in accounts if a['type'] == 'main'), None)
            if main_account:
                context += f"\n[SNS ACCOUNTS - {vtuber_name}]\n"
                context += f"Twitter/X: @{main_account['handle']}\n"

        # Get recent important posts (last 7 days, importance 4+)
        recent_posts = self.sns.get_recent_posts(vtuber_name, days=7, min_importance=4)
        if recent_posts:
            context += f"\n[RECENT IMPORTANT POSTS]\n"
            for post in recent_posts[:3]:  # Top 3
                context += f"- [{post['posted_at']}] {post['type']}: {post['content'][:100]}...\n"

        # Get upcoming activities
        activities = self.sns.get_upcoming_activities(vtuber_name, days_ahead=7)
        if activities:
            context += f"\n[UPCOMING ACTIVITIES]\n"
            for activity in activities[:3]:
                context += f"- [{activity['date']}] {activity['type']}: {activity['title']}\n"

        return context

    def close(self):
        """Close database connections"""
        if self.conn:
            self.conn.close()
        if self.restriction_checker:
            self.restriction_checker.close()
        if self.knowledge:
            self.knowledge.close()
        if self.sns:
            self.sns.close()


# Convenience function for quick context building
def build_context_for_chat(vtuber_name: str, db_path: Path = DB_PATH) -> Optional[str]:
    """
    Quick function to build context for chat

    Args:
        vtuber_name: VTuber name to talk about
        db_path: Database path

    Returns:
        str: System prompt addition
    """
    builder = ConversationContextBuilder(db_path)
    try:
        context = builder.get_recent_streams_context(vtuber_name)
        if context:
            return builder.build_system_prompt_addition(context)
        return None
    finally:
        builder.close()
