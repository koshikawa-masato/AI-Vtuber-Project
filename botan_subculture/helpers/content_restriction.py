"""
Content Restriction Helper
===========================

Hololive guideline compliance for Botan's conversations.

RULES:
1. Botan watches ALL streams/videos/shorts (100% knowledge)
2. BUT: Cannot reveal member-only or clip-prohibited content
3. When asked about restricted content: deflect with attitude

Example deflections:
- "推しメンなら知ってて当たり前っしょ？"
- "それ言っちゃったらダメなやつじゃん"
- "気になるなら自分でメン限入りなよ"
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


class ContentRestrictionChecker:
    """Check if content can be mentioned in conversation"""

    def __init__(self, db_path='subculture_knowledge.db'):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.conn = sqlite3.connect(str(self.db_path))

    def can_mention_stream(self, stream_id):
        """
        Check if a specific stream can be mentioned

        Args:
            stream_id: Stream ID from vtuber_streams table

        Returns:
            tuple: (can_mention: bool, reason: str)
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT
            title,
            is_member_only,
            is_clip_prohibited,
            content_visibility,
            is_ongoing,
            stream_end_time
        FROM vtuber_streams
        WHERE stream_id = ?
        """, (stream_id,))

        result = cursor.fetchone()
        if not result:
            return False, "stream_not_found"

        title, is_member_only, is_clip_prohibited, visibility, is_ongoing, stream_end_time = result

        # CRITICAL RULE: Ongoing stream: CANNOT mention
        if is_ongoing:
            return False, "stream_ongoing"

        # Member-only content: CANNOT mention
        if is_member_only or visibility == 'member':
            return False, "member_only"

        # Clip-prohibited content: CANNOT mention
        if is_clip_prohibited or visibility == 'restricted':
            return False, "clip_prohibited"

        # Public content: CAN mention
        return True, "public"

    def get_mentionable_streams(self, vtuber_id=None, days=7):
        """
        Get streams that can be mentioned in conversation

        Args:
            vtuber_id: VTuber ID (None = all VTubers)
            days: Number of days to look back

        Returns:
            list: List of (stream_id, vtuber_name, title, stream_date)
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        if vtuber_id:
            query = """
            SELECT
                s.stream_id,
                v.name,
                s.title,
                s.stream_date
            FROM vtuber_streams s
            JOIN vtubers v ON s.vtuber_id = v.vtuber_id
            WHERE s.vtuber_id = ?
              AND s.stream_date >= ?
              AND (s.is_ongoing = 0 OR s.is_ongoing IS NULL)
              AND (s.is_member_only = 0 OR s.is_member_only IS NULL)
              AND (s.is_clip_prohibited = 0 OR s.is_clip_prohibited IS NULL)
              AND (s.content_visibility = 'public' OR s.content_visibility IS NULL)
            ORDER BY s.stream_date DESC
            """
            cursor.execute(query, (vtuber_id, cutoff_date))
        else:
            query = """
            SELECT
                s.stream_id,
                v.name,
                s.title,
                s.stream_date
            FROM vtuber_streams s
            JOIN vtubers v ON s.vtuber_id = v.vtuber_id
            WHERE s.stream_date >= ?
              AND (s.is_ongoing = 0 OR s.is_ongoing IS NULL)
              AND (s.is_member_only = 0 OR s.is_member_only IS NULL)
              AND (s.is_clip_prohibited = 0 OR s.is_clip_prohibited IS NULL)
              AND (s.content_visibility = 'public' OR s.content_visibility IS NULL)
            ORDER BY s.stream_date DESC
            """
            cursor.execute(query, (cutoff_date,))

        return cursor.fetchall()

    def get_deflection_message(self, reason):
        """
        Get appropriate deflection message for restricted content

        Args:
            reason: Restriction reason (member_only, clip_prohibited)

        Returns:
            str: Deflection message in Botan's style
        """
        deflections = {
            'stream_ongoing': [
                "まだ配信中じゃん。終わってから話そうよ",
                "配信見ろよ！今まさにやってるんだから",
                "ネタバレになっちゃうでしょ。配信終わってから",
                "今配信中のやつ？それは配信見て確かめなよ"
            ],
            'member_only': [
                "推しメンなら知ってて当たり前っしょ？",
                "それメン限の話じゃん。言えるわけないでしょ",
                "気になるならメンバーシップ入りなよ",
                "メン限の内容は秘密に決まってんじゃん"
            ],
            'clip_prohibited': [
                "それ言っちゃったらダメなやつじゃん",
                "切り抜き禁止って知らないの？ルール守ろうよ",
                "その話は内緒ってことになってるから",
                "ホロライブのガイドライン読んだ？"
            ]
        }

        import random
        messages = deflections.get(reason, ["その話は内緒ね"])
        return random.choice(messages)

    def build_conversation_context(self, vtuber_name, days=3):
        """
        Build safe conversation context for a VTuber

        Args:
            vtuber_name: VTuber's name
            days: Number of days to look back

        Returns:
            dict: {
                'vtuber_id': int,
                'recent_streams': list of public streams,
                'can_mention_count': int,
                'total_streams': int
            }
        """
        cursor = self.conn.cursor()

        # Get VTuber ID
        cursor.execute("SELECT vtuber_id FROM vtubers WHERE name = ?", (vtuber_name,))
        result = cursor.fetchone()
        if not result:
            return None

        vtuber_id = result[0]
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Get all recent streams (Botan watched ALL of them)
        cursor.execute("""
        SELECT COUNT(*)
        FROM vtuber_streams
        WHERE vtuber_id = ?
          AND stream_date >= ?
        """, (vtuber_id, cutoff_date))
        total_streams = cursor.fetchone()[0]

        # Get mentionable streams
        mentionable_streams = self.get_mentionable_streams(vtuber_id, days)

        return {
            'vtuber_id': vtuber_id,
            'recent_streams': mentionable_streams,
            'can_mention_count': len(mentionable_streams),
            'total_streams': total_streams,
            'watched_all': True  # Botan ALWAYS watches everything
        }

    def check_conversation_safety(self, user_question, vtuber_name):
        """
        Check if user is asking about restricted content

        Args:
            user_question: User's question
            vtuber_name: VTuber being discussed

        Returns:
            dict: {
                'is_safe': bool,
                'reason': str,
                'deflection': str or None
            }
        """
        # Keywords that might indicate restricted content
        restricted_keywords = [
            'メン限', 'メンバー限定', 'メンバーシップ',
            '切り抜き禁止', '話せないこと', '内緒',
            'member only', 'members only'
        ]

        question_lower = user_question.lower()

        for keyword in restricted_keywords:
            if keyword in question_lower:
                return {
                    'is_safe': False,
                    'reason': 'restricted_content_mentioned',
                    'deflection': "そういう話は内緒に決まってんじゃん。ルール守ろうよ"
                }

        # Safe to answer
        return {
            'is_safe': True,
            'reason': 'public_content',
            'deflection': None
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Usage example for integration with chat system
def example_usage():
    """Example of how to use this in chat_with_botan_memories.py"""

    checker = ContentRestrictionChecker()

    # Scenario 1: User asks about recent stream
    print("=" * 60)
    print("Scenario 1: Recent stream check")
    print("=" * 60)

    context = checker.build_conversation_context('さくらみこ', days=3)
    if context:
        print(f"Total streams (last 3 days): {context['total_streams']}")
        print(f"Can mention: {context['can_mention_count']}")
        print(f"Watched all: {context['watched_all']}")

        if context['recent_streams']:
            print("\nMentionable streams:")
            for stream_id, name, title, date in context['recent_streams'][:3]:
                print(f"  - [{date}] {title}")

    # Scenario 2: User asks about member content
    print("\n" + "=" * 60)
    print("Scenario 2: Restricted content check")
    print("=" * 60)

    user_question = "昨日のメン限配信どうだった？"
    safety = checker.check_conversation_safety(user_question, 'さくらみこ')

    print(f"Question: {user_question}")
    print(f"Is safe: {safety['is_safe']}")
    if not safety['is_safe']:
        print(f"Deflection: {safety['deflection']}")

    checker.close()


if __name__ == "__main__":
    example_usage()
