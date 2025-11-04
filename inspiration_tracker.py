"""
Inspiration Tracker
Tracks "truth from lies" (嘘から出た実) - hallucinations that grow into real values

Author: Claude Code (Design & Implementation)
Created: 2025-10-24
Version: 1.0
"""

import sqlite3
from typing import Optional, List, Dict
from datetime import datetime


class InspirationTracker:
    """
    Tracks inspiration events - hallucinations that may grow into real values/goals

    Status progression:
    - seed: Initial mention (hallucination)
    - growing: Repeated mentions (confidence increasing)
    - realized: Actual action taken (became reality)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Create inspiration_events table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspiration_events (
                inspiration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                character TEXT NOT NULL,
                original_hallucination TEXT NOT NULL,
                event_id_origin INTEGER NOT NULL,
                inspired_value TEXT NOT NULL,
                event_id_realization INTEGER,
                status TEXT DEFAULT 'seed',
                confidence REAL DEFAULT 0.0,
                mention_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                realized_at TIMESTAMP,
                FOREIGN KEY (event_id_origin) REFERENCES sister_shared_events(event_id)
            )
        ''')

        conn.commit()
        conn.close()

    def record_inspiration_seed(
        self,
        character: str,
        hallucination: str,
        event_id: int,
        inspired_value: str,
        initial_confidence: float = 0.3
    ) -> int:
        """
        Record the initial seed of inspiration

        Args:
            character: Character name (botan/kasho/yuri)
            hallucination: Original hallucinated statement
            event_id: Event where this occurred
            inspired_value: The aspirational value/goal
            initial_confidence: Initial confidence (default 0.3)

        Returns:
            inspiration_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if similar inspiration already exists
        existing = self._find_similar_inspiration(character, inspired_value)

        if existing:
            # Grow existing inspiration
            inspiration_id = existing['inspiration_id']
            self.grow_inspiration(inspiration_id)
            conn.close()
            return inspiration_id

        # Create new inspiration seed
        cursor.execute('''
            INSERT INTO inspiration_events (
                character, original_hallucination,
                event_id_origin, inspired_value,
                status, confidence
            ) VALUES (?, ?, ?, ?, 'seed', ?)
        ''', (character, hallucination, event_id, inspired_value, initial_confidence))

        inspiration_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"[INSPIRATION SEED] {character}: '{inspired_value}' (ID: {inspiration_id})")
        return inspiration_id

    def grow_inspiration(self, inspiration_id: int):
        """
        Grow inspiration (called when mentioned again)

        Increases confidence and updates status if threshold reached
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current state
        cursor.execute('''
            SELECT confidence, mention_count, status, character, inspired_value
            FROM inspiration_events
            WHERE inspiration_id = ?
        ''', (inspiration_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        current_confidence, mention_count, status, character, inspired_value = row

        # Increase confidence and mention count
        new_confidence = min(1.0, current_confidence + 0.1)
        new_mention_count = mention_count + 1

        # Update status based on confidence
        new_status = status
        if new_confidence >= 0.7 and status == 'seed':
            new_status = 'growing'
        elif new_confidence >= 0.9 and status == 'growing':
            # Still growing, but very close to realization
            new_status = 'growing'

        cursor.execute('''
            UPDATE inspiration_events
            SET confidence = ?,
                mention_count = ?,
                status = ?,
                last_mentioned_at = CURRENT_TIMESTAMP
            WHERE inspiration_id = ?
        ''', (new_confidence, new_mention_count, new_status, inspiration_id))

        conn.commit()
        conn.close()

        print(f"[INSPIRATION GROW] {character}: '{inspired_value}' (mentions: {new_mention_count}, confidence: {new_confidence:.2f}, status: {new_status})")

    def realize_inspiration(
        self,
        inspiration_id: int,
        event_id_realization: int
    ):
        """
        Mark inspiration as realized (became reality)

        Args:
            inspiration_id: Inspiration ID
            event_id_realization: Event where it was realized
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get inspiration details
        cursor.execute('''
            SELECT character, inspired_value
            FROM inspiration_events
            WHERE inspiration_id = ?
        ''', (inspiration_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        character, inspired_value = row

        cursor.execute('''
            UPDATE inspiration_events
            SET status = 'realized',
                event_id_realization = ?,
                realized_at = CURRENT_TIMESTAMP,
                confidence = 1.0
            WHERE inspiration_id = ?
        ''', (event_id_realization, inspiration_id))

        conn.commit()
        conn.close()

        print(f"[INSPIRATION REALIZED] {character}: '{inspired_value}' became reality! (Event #{event_id_realization})")

    def _find_similar_inspiration(
        self,
        character: str,
        inspired_value: str
    ) -> Optional[Dict]:
        """Find similar existing inspiration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Simple similarity: check if key words match
        # Extract key words from inspired_value
        key_words = [word for word in inspired_value.split() if len(word) > 2][:3]

        cursor.execute('''
            SELECT inspiration_id, inspired_value, confidence, mention_count, status
            FROM inspiration_events
            WHERE character = ?
                AND status != 'realized'
            ORDER BY created_at DESC
        ''', (character,))

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            inspiration_id, existing_value, confidence, mention_count, status = row
            # Simple keyword matching
            if any(word in existing_value for word in key_words):
                return {
                    'inspiration_id': inspiration_id,
                    'inspired_value': existing_value,
                    'confidence': confidence,
                    'mention_count': mention_count,
                    'status': status
                }

        return None

    def get_inspirations_by_character(
        self,
        character: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all inspirations for a character

        Args:
            character: Character name
            status: Filter by status (seed/growing/realized), None for all

        Returns:
            List of inspiration records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT inspiration_id, original_hallucination, event_id_origin,
                       inspired_value, status, confidence, mention_count,
                       created_at, last_mentioned_at, realized_at
                FROM inspiration_events
                WHERE character = ? AND status = ?
                ORDER BY last_mentioned_at DESC
            ''', (character, status))
        else:
            cursor.execute('''
                SELECT inspiration_id, original_hallucination, event_id_origin,
                       inspired_value, status, confidence, mention_count,
                       created_at, last_mentioned_at, realized_at
                FROM inspiration_events
                WHERE character = ?
                ORDER BY last_mentioned_at DESC
            ''', (character,))

        rows = cursor.fetchall()
        conn.close()

        inspirations = []
        for row in rows:
            inspirations.append({
                'inspiration_id': row[0],
                'original_hallucination': row[1],
                'event_id_origin': row[2],
                'inspired_value': row[3],
                'status': row[4],
                'confidence': row[5],
                'mention_count': row[6],
                'created_at': row[7],
                'last_mentioned_at': row[8],
                'realized_at': row[9]
            })

        return inspirations

    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total by status
        cursor.execute('''
            SELECT status, COUNT(*), AVG(confidence)
            FROM inspiration_events
            GROUP BY status
        ''')
        for row in cursor.fetchall():
            status, count, avg_confidence = row
            stats[status] = {
                'count': count,
                'avg_confidence': avg_confidence
            }

        # Total by character
        cursor.execute('''
            SELECT character, COUNT(*), AVG(confidence)
            FROM inspiration_events
            GROUP BY character
        ''')
        stats['by_character'] = {}
        for row in cursor.fetchall():
            character, count, avg_confidence = row
            stats['by_character'][character] = {
                'count': count,
                'avg_confidence': avg_confidence
            }

        conn.close()
        return stats


# Test code
if __name__ == "__main__":
    print("=== InspirationTracker Test ===\n")

    # Use test database
    tracker = InspirationTracker(db_path="test_inspiration.db")

    # Test 1: Record seed
    id1 = tracker.record_inspiration_seed(
        character='botan',
        hallucination='視聴者さんたちと話す時間を作りたいな！',
        event_id=136,
        inspired_value='視聴者との交流を大切にしたい'
    )

    # Test 2: Grow inspiration (repeated mention)
    tracker.grow_inspiration(id1)
    tracker.grow_inspiration(id1)

    # Test 3: Record another seed
    id2 = tracker.record_inspiration_seed(
        character='kasho',
        hallucination='配信でゲームをやってみたい',
        event_id=137,
        inspired_value='配信でゲーム実況をしたい'
    )

    # Test 4: Realize inspiration
    tracker.realize_inspiration(
        inspiration_id=id1,
        event_id_realization=150
    )

    # Test 5: Get all inspirations
    print("\n=== Botan's Inspirations ===")
    inspirations = tracker.get_inspirations_by_character('botan')
    for insp in inspirations:
        print(f"ID {insp['inspiration_id']}: {insp['inspired_value']}")
        print(f"  Status: {insp['status']}, Confidence: {insp['confidence']:.2f}, Mentions: {insp['mention_count']}")
        print()

    # Test 6: Statistics
    print("=== Statistics ===")
    stats = tracker.get_statistics()
    print(f"Statistics: {stats}")

    # Cleanup
    import os
    os.remove("test_inspiration.db")
    print("\n✅ All tests completed")
