"""
Copy Robot Checker - Sensitive Content and Vocabulary Analysis
Created: 2025-10-27
Purpose: Check Copy Robot DB for sensitive content and vocabulary usage
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.filter import Layer1PreFilter


class CopyRobotChecker:
    """
    Copy Robot Sensitive Content and Vocabulary Checker

    Scans Copy Robot DB (sisters_memory.db copy) for:
    1. Sensitive/NG words in Events and Memories
    2. Vocabulary usage analysis (learned words from youtube_learning.db)
    """

    def __init__(self,
                 copy_robot_db_path: str,
                 youtube_learning_db_path: str = None,
                 sensitive_db_path: str = None):
        """
        Initialize

        Args:
            copy_robot_db_path: Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db
            youtube_learning_db_path: Path to youtube_learning.db
            sensitive_db_path: Path to sensitive_filter.db
        """
        self.copy_robot_db = copy_robot_db_path

        if youtube_learning_db_path is None:
            youtube_learning_db_path = "/home/koshikawa/toExecUnit/youtube_learning_system/database/youtube_learning.db"
        self.youtube_learning_db = youtube_learning_db_path

        # Initialize sensitive filter
        self.filter = Layer1PreFilter(db_path=sensitive_db_path)

        # Statistics
        self.stats = {
            'events_scanned': 0,
            'memories_scanned': 0,
            'total_text_items': 0,
            'sensitive_detected': 0,
            'ng_words_found': defaultdict(int)
        }

        # Detection results
        self.sensitive_results = []

    def scan_copy_robot(self) -> Dict:
        """
        Scan Copy Robot DB for sensitive content

        Returns:
            {
                'events': List[Dict],  # Event scan results
                'memories': {
                    'botan': List[Dict],
                    'kasho': List[Dict],
                    'yuri': List[Dict]
                },
                'statistics': Dict,
                'ng_word_summary': Dict
            }
        """
        results = {
            'events': [],
            'memories': {
                'botan': [],
                'kasho': [],
                'yuri': []
            },
            'statistics': {},
            'ng_word_summary': {}
        }

        # Scan Events
        results['events'] = self._scan_events()

        # Scan Memories (three sisters)
        for character in ['botan', 'kasho', 'yuri']:
            results['memories'][character] = self._scan_memories(character)

        # Generate statistics
        results['statistics'] = self.stats.copy()
        results['ng_word_summary'] = dict(self.stats['ng_words_found'])

        return results

    def _scan_events(self) -> List[Dict]:
        """
        Scan sister_shared_events table

        Returns:
            List of events with detected sensitive content
        """
        conn = sqlite3.connect(self.copy_robot_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT event_id, event_number, event_name, event_date,
                   description, participants, cultural_context
            FROM sister_shared_events
            ORDER BY event_number
        """)

        events = cursor.fetchall()
        conn.close()

        detected_events = []

        for event in events:
            self.stats['events_scanned'] += 1

            event_id = event[0]
            event_number = event[1]
            event_name = event[2]
            event_date = event[3]

            # Scan text fields
            text_fields = {
                'event_name': event[2],
                'description': event[4],
                'participants': event[5],
                'cultural_context': event[6]
            }

            # Check each field
            event_detections = []
            for field_name, text in text_fields.items():
                if text:
                    self.stats['total_text_items'] += 1
                    result = self.filter.filter_comment(text)

                    if result['detected_words']:
                        self.stats['sensitive_detected'] += 1

                        for ng in result['detected_words']:
                            self.stats['ng_words_found'][ng['word']] += 1

                        event_detections.append({
                            'field': field_name,
                            'text': text[:100] + '...' if len(text) > 100 else text,
                            'action': result['action'],
                            'detected_words': result['detected_words'],
                            'max_severity': result['max_severity']
                        })

            if event_detections:
                detected_events.append({
                    'event_id': event_id,
                    'event_number': event_number,
                    'event_name': event_name,
                    'event_date': event_date,
                    'detections': event_detections
                })

        return detected_events

    def _scan_memories(self, character: str) -> List[Dict]:
        """
        Scan character-specific memories table

        Args:
            character: 'botan', 'kasho', or 'yuri'

        Returns:
            List of memories with detected sensitive content
        """
        table_name = f"{character}_memories"

        conn = sqlite3.connect(self.copy_robot_db)
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT memory_id, event_id, memory_date,
                       {character}_emotion, {character}_action, {character}_thought, diary_entry
                FROM {table_name}
                ORDER BY memory_date
            """)

            memories = cursor.fetchall()
            conn.close()

        except sqlite3.OperationalError:
            # Table doesn't exist
            conn.close()
            return []

        detected_memories = []

        for memory in memories:
            self.stats['memories_scanned'] += 1

            memory_id = memory[0]
            event_id = memory[1]
            memory_date = memory[2]

            # Scan text fields
            text_fields = {
                f'{character}_emotion': memory[3],
                f'{character}_action': memory[4],
                f'{character}_thought': memory[5],
                'diary_entry': memory[6]
            }

            # Check each field
            memory_detections = []
            for field_name, text in text_fields.items():
                if text:
                    self.stats['total_text_items'] += 1
                    result = self.filter.filter_comment(text)

                    if result['detected_words']:
                        self.stats['sensitive_detected'] += 1

                        for ng in result['detected_words']:
                            self.stats['ng_words_found'][ng['word']] += 1

                        memory_detections.append({
                            'field': field_name,
                            'text': text[:100] + '...' if len(text) > 100 else text,
                            'action': result['action'],
                            'detected_words': result['detected_words'],
                            'max_severity': result['max_severity']
                        })

            if memory_detections:
                detected_memories.append({
                    'memory_id': memory_id,
                    'event_id': event_id,
                    'memory_date': memory_date,
                    'detections': memory_detections
                })

        return detected_memories

    def analyze_vocabulary_usage(self) -> Dict:
        """
        Analyze vocabulary usage in Copy Robot DB

        Checks:
        1. Which learned words are used in Events/Memories
        2. How frequently each word is used
        3. Context of usage

        Returns:
            {
                'botan': {
                    'learned_words': int,
                    'used_in_robot': int,
                    'usage_details': List[Dict]
                },
                'kasho': {...},
                'yuri': {...}
            }
        """
        analysis = {
            'botan': {'learned_words': 0, 'used_in_robot': 0, 'usage_details': []},
            'kasho': {'learned_words': 0, 'used_in_robot': 0, 'usage_details': []},
            'yuri': {'learned_words': 0, 'used_in_robot': 0, 'usage_details': []}
        }

        # Load learned vocabulary from youtube_learning.db
        try:
            conn = sqlite3.connect(self.youtube_learning_db)
            cursor = conn.cursor()

            for character in ['botan', 'kasho', 'yuri']:
                cursor.execute("""
                    SELECT word, meaning
                    FROM word_knowledge
                    WHERE learned_by = ?
                """, (character,))

                learned_words = cursor.fetchall()
                analysis[character]['learned_words'] = len(learned_words)

                # Check usage in Copy Robot DB
                usage_details = []
                for word, meaning in learned_words:
                    usage_count = self._count_word_usage(character, word)
                    if usage_count > 0:
                        analysis[character]['used_in_robot'] += 1
                        usage_details.append({
                            'word': word,
                            'meaning': meaning[:50] + '...' if meaning and len(meaning) > 50 else meaning,
                            'usage_count': usage_count
                        })

                analysis[character]['usage_details'] = sorted(
                    usage_details,
                    key=lambda x: x['usage_count'],
                    reverse=True
                )

            conn.close()

        except Exception as e:
            print(f"[ERROR] Failed to analyze vocabulary: {e}")

        return analysis

    def _count_word_usage(self, character: str, word: str) -> int:
        """
        Count word usage in Copy Robot DB

        Args:
            character: 'botan', 'kasho', or 'yuri'
            word: Word to search

        Returns:
            Usage count
        """
        conn = sqlite3.connect(self.copy_robot_db)
        cursor = conn.cursor()

        count = 0

        # Search in Events
        cursor.execute("""
            SELECT description, participants, cultural_context
            FROM sister_shared_events
        """)

        for row in cursor.fetchall():
            for text in row:
                if text and word in text:
                    count += 1

        # Search in character's memories
        table_name = f"{character}_memories"

        try:
            cursor.execute(f"""
                SELECT {character}_emotion, {character}_action, {character}_thought, diary_entry
                FROM {table_name}
            """)

            for row in cursor.fetchall():
                for text in row:
                    if text and word in text:
                        count += 1

        except sqlite3.OperationalError:
            pass  # Table doesn't exist

        conn.close()
        return count


# Test
if __name__ == "__main__":
    copy_robot_db = "/home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db"

    checker = CopyRobotChecker(copy_robot_db)

    print("=== Copy Robot Checker Test ===\n")

    # Scan for sensitive content
    print("[1] Scanning for sensitive content...")
    results = checker.scan_copy_robot()

    print(f"\nStatistics:")
    print(f"  Events scanned: {results['statistics']['events_scanned']}")
    print(f"  Memories scanned: {results['statistics']['memories_scanned']}")
    print(f"  Text items: {results['statistics']['total_text_items']}")
    print(f"  Sensitive detected: {results['statistics']['sensitive_detected']}")

    if results['ng_word_summary']:
        print(f"\nNG Words Found:")
        for word, count in sorted(results['ng_word_summary'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {word}: {count} times")

    # Analyze vocabulary
    print("\n[2] Analyzing vocabulary usage...")
    vocab_analysis = checker.analyze_vocabulary_usage()

    for character in ['botan', 'kasho', 'yuri']:
        print(f"\n{character.upper()}:")
        print(f"  Learned words: {vocab_analysis[character]['learned_words']}")
        print(f"  Used in Copy Robot: {vocab_analysis[character]['used_in_robot']}")

        if vocab_analysis[character]['usage_details']:
            print(f"  Top used words:")
            for detail in vocab_analysis[character]['usage_details'][:5]:
                print(f"    - {detail['word']}: {detail['usage_count']} times")
