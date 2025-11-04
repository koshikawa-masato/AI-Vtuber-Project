#!/usr/bin/env python3
"""
Evaluate Botan's generated memories
"""

import sqlite3
import json
from typing import Dict, List

class BotanMemoryEvaluator:
    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db"):
        self.db_path = db_path

    def get_memory_sample(self, event_ids: List[int]) -> List[Dict]:
        """Get specific memories for evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = []
        for event_id in event_ids:
            # Get objective event
            cursor.execute("""
                SELECT botan_absolute_day, event_name, category, description
                FROM sister_shared_events
                WHERE event_id = ?
            """, (event_id,))
            event_row = cursor.fetchone()

            if not event_row:
                continue

            # Get Botan's subjective memory
            cursor.execute("""
                SELECT botan_emotion, botan_action, botan_thought,
                       diary_entry, kasho_observed_behavior, kasho_inferred_feeling
                FROM botan_memories
                WHERE event_id = ?
            """, (event_id,))
            memory_row = cursor.fetchone()

            if not memory_row:
                continue

            # Calculate age from absolute_day
            absolute_day = event_row[0]
            age_years = absolute_day // 365
            age_months = (absolute_day % 365) // 30

            results.append({
                'event_id': event_id,
                'absolute_day': absolute_day,
                'age': f"{age_years}歳{age_months}ヶ月",
                'event_name': event_row[1],
                'event_category': event_row[2],
                'description': event_row[3],
                'botan_subjective': {
                    'emotion': memory_row[0],
                    'action': memory_row[1],
                    'thought': memory_row[2],
                    'diary': memory_row[3],
                    'kasho_observed': memory_row[4],
                    'kasho_inferred': memory_row[5]
                }
            })

        conn.close()
        return results

    def print_evaluation_report(self, sample_events: List[int]):
        """Print detailed evaluation report"""
        memories = self.get_memory_sample(sample_events)

        print("=" * 80)
        print("牡丹の記憶 品質評価レポート")
        print("=" * 80)
        print()

        for i, mem in enumerate(memories, 1):
            print(f"【サンプル {i}/{len(memories)}】")
            print(f"Event ID: {mem['event_id']}")
            print(f"日齢: {mem['absolute_day']}日 ({mem['age']})")
            print(f"イベント: {mem['event_name']}")
            print(f"カテゴリ: {mem['event_category']}")
            print()
            print("--- 牡丹の主観的記憶 ---")
            print(f"感情: {mem['botan_subjective']['emotion']}")
            print(f"行動: {mem['botan_subjective']['action']}")
            print(f"思考: {mem['botan_subjective']['thought']}")
            print()
            print(f"日記:")
            print(f"  {mem['botan_subjective']['diary']}")
            print()
            print(f"叶翔の観察:")
            print(f"  行動: {mem['botan_subjective']['kasho_observed']}")
            print(f"  推測: {mem['botan_subjective']['kasho_inferred']}")
            print()
            print("-" * 80)
            print()

    def get_statistics(self):
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) FROM botan_memories")
        total = cursor.fetchone()[0]

        # Count by age range
        age_ranges = []
        for start, end, label in [
            (0, 365*2, "0-2歳 (乳幼児)"),
            (365*3, 365*10, "3-10歳 (LA期)"),
            (365*11, 365*14, "11-14歳 (帰国〜中学)"),
            (365*15, 365*17+365, "15-17歳 (高校〜現在)")
        ]:
            cursor.execute("""
                SELECT COUNT(*)
                FROM botan_memories bm
                JOIN sister_shared_events sse ON bm.event_id = sse.event_id
                WHERE sse.botan_absolute_day >= ? AND sse.botan_absolute_day < ?
            """, (start, end))
            count = cursor.fetchone()[0]
            age_ranges.append((label, count))

        conn.close()

        print("=" * 80)
        print("統計情報")
        print("=" * 80)
        print(f"総記憶数: {total}/98")
        print()
        print("年齢別分布:")
        for label, count in age_ranges:
            print(f"  {label}: {count}件")
        print("=" * 80)
        print()

if __name__ == "__main__":
    evaluator = BotanMemoryEvaluator()

    # Key life events to sample
    sample_events = [
        2,   # Birth (0歳)
        17,  # LA move (3歳)
        25,  # Japan return (10歳)
        36,  # Gyaru transformation (12歳)
        44,  # VTuber discovery (15歳)
        92   # Current (17歳)
    ]

    # Print statistics
    evaluator.get_statistics()

    # Print detailed evaluation
    evaluator.print_evaluation_report(sample_events)
