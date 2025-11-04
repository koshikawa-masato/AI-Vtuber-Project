#!/usr/bin/env python3
"""
BotanIdentity: Botan's Memory and Identity Module
Loads past life events from sisters_memory.db
Ensures identity continuity across sessions
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class BotanIdentity:
    """Botan's identity and memory system"""

    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db"):
        """Initialize Botan's identity"""
        self.db_path = db_path
        self.birthdate = datetime.strptime("2008-05-04", "%Y-%m-%d")
        self.current_age_years = 17
        self.current_age_days = 5  # Approximate

        # Load identity data
        self.major_events = self._load_major_events()
        self.total_events = len(self.major_events)

        print(f"[BotanIdentity] Initialized")
        print(f"[BotanIdentity] Birthdate: {self.birthdate.strftime('%Y-%m-%d')}")
        print(f"[BotanIdentity] Current Age: {self.current_age_years} years")
        print(f"[BotanIdentity] Major Events Loaded: {self.total_events}")

    def _load_major_events(self) -> List[Dict]:
        """Load major events from database"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Load all events where Botan participated
        cursor.execute("""
            SELECT *
            FROM sister_shared_events
            WHERE botan_absolute_day IS NOT NULL
            ORDER BY botan_absolute_day
        """)

        events = []
        for row in cursor.fetchall():
            event = dict(row)
            events.append(event)

        conn.close()

        return events

    def get_event_by_number(self, event_number: int) -> Optional[Dict]:
        """Get event by event number (001-100)"""

        for event in self.major_events:
            if event.get('event_number') == event_number:
                return event

        return None

    def get_events_by_age(self, age_years: int) -> List[Dict]:
        """Get events that occurred at a specific age"""

        events = []
        for event in self.major_events:
            if event.get('botan_age_years') == age_years:
                events.append(event)

        return events

    def get_events_by_category(self, category: str) -> List[Dict]:
        """Get events by category"""

        events = []
        for event in self.major_events:
            if event.get('category') == category:
                events.append(event)

        return events

    def get_events_by_location(self, location: str) -> List[Dict]:
        """Get events by location"""

        events = []
        for event in self.major_events:
            if event.get('location') == location:
                events.append(event)

        return events

    def get_la_period_events(self) -> List[Dict]:
        """Get events during LA period (age 3-10)"""

        la_events = []
        for event in self.major_events:
            age = event.get('botan_age_years')
            if age and 3 <= age <= 10:
                la_events.append(event)

        return la_events

    def recall_memory(self, query: str) -> List[Dict]:
        """Recall memories based on query"""

        # Simple keyword matching
        query_lower = query.lower()

        matches = []
        for event in self.major_events:
            event_name = event.get('event_name', '').lower()
            description = event.get('description', '').lower()

            if query_lower in event_name or query_lower in description:
                matches.append(event)

        return matches

    def format_event_for_prompt(self, event: Dict) -> str:
        """Format event for LLM prompt"""

        formatted = f"""
Event: {event.get('event_name')}
Date: {event.get('event_date')}
Botan's Age: {event.get('botan_age_years')} years {event.get('botan_age_days')} days
Location: {event.get('location')}
What Happened: {event.get('description')}
Emotional Impact: {event.get('emotional_impact')}/10
"""

        return formatted.strip()

    def get_identity_summary(self) -> str:
        """Get summary of Botan's identity"""

        summary = f"""
=== Botan's Identity ===
Name: 牡丹 (Botan)
Birthdate: {self.birthdate.strftime('%Y-%m-%d')} (2008-05-04)
Current Age: {self.current_age_years} years
Total Major Events: {self.total_events}

Key Periods:
- Early Childhood (Japan): 0-3 years
- LA Period: 3-10 years (2011-2018)
- Return to Japan: 10-{self.current_age_years} years (2018-present)

Event Categories:
- Life Turning Points: {len(self.get_events_by_category('life_turning_point'))}
- Sisterhood: {len(self.get_events_by_category('sisterhood'))}
- Encounters: {len(self.get_events_by_category('encounter'))}
- Difficulties: {len(self.get_events_by_category('difficulty'))}
- Moving Moments: {len(self.get_events_by_category('moving'))}
- Growth Moments: {len(self.get_events_by_category('growth'))}
- Cultural Influences: {len(self.get_events_by_category('cultural'))}

LA Period Events: {len(self.get_la_period_events())}
"""

        return summary.strip()

    def answer_memory_question(self, question: str) -> str:
        """Answer a question about Botan's memories"""

        # Example: "5歳の頃の記憶ある？"
        if "5歳" in question or "5 years old" in question.lower():
            events_age_5 = self.get_events_by_age(5)

            if not events_age_5:
                return "5歳の頃の記憶...あんまりハッキリ覚えてないかも〜"

            # Return most impactful event
            events_age_5.sort(key=lambda x: x.get('emotional_impact', 0), reverse=True)
            top_event = events_age_5[0]

            response = f"""5歳の頃？あ〜、{top_event.get('event_name')}！
マジで{top_event.get('description', '')}
{top_event.get('location')}にいた頃だね。
感情的インパクト: {top_event.get('emotional_impact')}/10 だったから、結構覚えてる！"""

            return response

        # Generic recall
        memories = self.recall_memory(question)

        if not memories:
            return "う〜ん、その記憶はちょっと思い出せないかも...ごめん！"

        # Return first match
        event = memories[0]
        return f"あ、{event.get('event_name')}のこと？{event.get('description')}"


def test_botan_identity():
    """Test BotanIdentity module"""

    print("=== Testing BotanIdentity ===\n")

    # Initialize
    botan = BotanIdentity()

    print("\n" + "="*50)
    print(botan.get_identity_summary())
    print("="*50)

    # Test: Get event by number
    print("\n[TEST] Get Event 082 (VTuber dream origin):")
    event_082 = botan.get_event_by_number(82)
    if event_082:
        print(botan.format_event_for_prompt(event_082))

    # Test: Get events at age 5
    print("\n[TEST] Get events at age 5:")
    events_age_5 = botan.get_events_by_age(5)
    print(f"Found {len(events_age_5)} events at age 5")
    for event in events_age_5[:3]:  # Show first 3
        print(f"  - {event.get('event_name')}")

    # Test: Answer memory question
    print("\n[TEST] Answer question: '5歳の頃の記憶ある？'")
    response = botan.answer_memory_question("5歳の頃の記憶ある？")
    print(f"Botan: {response}")

    # Test: LA period events
    print("\n[TEST] LA Period Events:")
    la_events = botan.get_la_period_events()
    print(f"Found {len(la_events)} events during LA period (age 3-10)")

    print("\n[SUCCESS] BotanIdentity module test complete!")


if __name__ == "__main__":
    test_botan_identity()
