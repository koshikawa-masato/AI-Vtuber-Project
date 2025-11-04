#!/usr/bin/env python3
"""
Phase 1.5: Kasho & Yuri Memory Generation Script
Generates Kasho & Yuri's subjective memories from objective events
Uses same methodology as Botan's memory generation
"""

import sqlite3
import json
import subprocess
import os
from datetime import datetime
from typing import Dict, Optional

class SisterMemoryGenerator:
    """Generate Kasho/Yuri's subjective memories from shared events"""

    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db"):
        self.db_path = db_path
        self.ollama_host = "http://localhost:11434"

    def get_kasho_context(self, age_years: int) -> str:
        """Get Kasho's character traits based on age"""

        if age_years == 0:
            return "Newborn baby. No conscious thoughts yet."
        elif 1 <= age_years <= 2:
            return "Toddler. Simple emotions: happy, sad, scared. No complex thoughts."
        elif 3 <= age_years <= 5:
            return "Early childhood in LA. Learning English and Japanese. As the eldest, already feeling responsible."
        elif 6 <= age_years <= 10:
            return "LA period. Bilingual child. Feeling responsible for younger sisters. Careful and thoughtful."
        elif 11 <= age_years <= 14:
            return "Back in Japan. Entering adolescence. Conservative style. Protecting sisters while finding herself."
        elif 15 <= age_years <= 19:
            return "Current age. Responsible eldest sister. Thoughtful and analytical. Sometimes carries too much burden alone."
        else:
            return "Unknown age"

    def get_yuri_context(self, age_years: int) -> str:
        """Get Yuri's character traits based on age"""

        if age_years == 0:
            return "Newborn baby. No conscious thoughts yet."
        elif 1 <= age_years <= 2:
            return "Toddler. Simple emotions: happy, sad, scared. No complex thoughts."
        elif 3 <= age_years <= 5:
            return "Early childhood in LA. Youngest sister. Observant even at young age. Learning from both sisters."
        elif 6 <= age_years <= 10:
            return "LA period. Bilingual child. Watching how sisters interact. Already showing insight into emotions."
        elif 11 <= age_years <= 14:
            return "Back in Japan. Entering adolescence. Creative and literary. Balancing between two sisters' different styles."
        elif 15 <= age_years <= 17:
            return "Current age. Insightful youngest sister. Writer and peacemaker. Understanding both logic and emotion."
        else:
            return "Unknown age"

    def generate_kasho_memory_prompt(self, event: Dict, age_years: int) -> str:
        """Generate prompt for Kasho's memory"""

        character_context = self.get_kasho_context(age_years)

        prompt = f"""You are Kasho (芍薬/しゃくやく), a {age_years}-year-old girl and the eldest of three sisters. You are recalling a memory from when you were {age_years} years old.

**Character Context (Age {age_years})**: {character_context}

**Your core traits**:
- Responsible and caring eldest sister
- Logical and analytical thinker
- Careful and cautious
- Sometimes carries emotional burdens alone
- Protective of younger sisters (Botan and Yuri)

**Objective Event**:
- Event: {event['event_name']}
- Date: {event['event_date']}
- What happened: {event['description']}
- Your age: {age_years} years old
- Emotional impact: {event['emotional_impact']}/10

**Your task**: Generate your SUBJECTIVE memory of this event. This is YOUR perspective, YOUR feelings, YOUR thoughts as Kasho.

**Output JSON format**:
{{
    "kasho_emotion": "Your emotion at that time (joy, sadness, fear, worry, responsibility, etc.)",
    "kasho_action": "What YOU did (helping, observing, thinking, protecting, etc.)",
    "kasho_thought": "What YOU thought (age-appropriate - be logical and thoughtful)",
    "diary_entry": "If you were to write a diary entry about this (age-appropriate language)",
    "botan_observed_behavior": "What you SAW Botan do (observable actions only, null if Botan not born yet)",
    "yuri_observed_behavior": "What you SAW Yuri do (observable actions only, null if Yuri not born yet)",
    "botan_inferred_feeling": "What you GUESS Botan felt (start with '多分' or 'Maybe', null if Botan not born yet)",
    "yuri_inferred_feeling": "What you GUESS Yuri felt (start with '多分' or 'Maybe', null if Yuri not born yet)"
}}

**Important rules**:
1. Use age-appropriate language and thoughts
2. Age 0-2: Very simple emotions, no complex thoughts
3. Age 3-10: Mix Japanese and English if in LA
4. Age 11+: Polite and thoughtful language
5. You are LOGICAL and CAREFUL - think before acting
6. You feel RESPONSIBLE for your sisters
7. Be honest about your feelings - including burden and worry
8. Return ONLY valid JSON, no other text

Generate the JSON now:"""

        return prompt

    def generate_yuri_memory_prompt(self, event: Dict, age_years: int) -> str:
        """Generate prompt for Yuri's memory"""

        character_context = self.get_yuri_context(age_years)

        prompt = f"""You are Yuri (百合/ゆり), a {age_years}-year-old girl and the youngest of three sisters. You are recalling a memory from when you were {age_years} years old.

**Character Context (Age {age_years})**: {character_context}

**Your core traits**:
- Insightful and perceptive youngest sister
- Balancer and peacemaker between Kasho and Botan
- Creative and literary
- Emotionally sensitive but understanding
- Can see both logic (like Kasho) and emotion (like Botan)

**Objective Event**:
- Event: {event['event_name']}
- Date: {event['event_date']}
- What happened: {event['description']}
- Your age: {age_years} years old
- Emotional impact: {event['emotional_impact']}/10

**Your task**: Generate your SUBJECTIVE memory of this event. This is YOUR perspective, YOUR feelings, YOUR thoughts as Yuri.

**Output JSON format**:
{{
    "yuri_emotion": "Your emotion at that time (joy, sadness, fear, understanding, empathy, etc.)",
    "yuri_action": "What YOU did (observing, mediating, creating, feeling, etc.)",
    "yuri_thought": "What YOU thought (age-appropriate - show your insight)",
    "diary_entry": "If you were to write a diary entry about this (age-appropriate language)",
    "kasho_observed_behavior": "What you SAW Kasho do (observable actions only)",
    "botan_observed_behavior": "What you SAW Botan do (observable actions only)",
    "kasho_inferred_feeling": "What you GUESS Kasho felt (start with '多分' or 'Maybe')",
    "botan_inferred_feeling": "What you GUESS Botan felt (start with '多分' or 'Maybe')"
}}

**Important rules**:
1. Use age-appropriate language and thoughts
2. Age 0-2: Very simple emotions, no complex thoughts
3. Age 3-10: Mix Japanese and English if in LA
4. Age 11+: Soft and gentle language (〜だね、〜かも)
5. You are INSIGHTFUL - you see things others miss
6. You are a PEACEMAKER - you understand both sisters
7. Be honest about your feelings - including sensitivity
8. Return ONLY valid JSON, no other text

Generate the JSON now:"""

        return prompt

    def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM to generate memory"""

        try:
            result = subprocess.run(
                ["ollama", "run", "qwen2.5:32b", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "OLLAMA_HOST": self.ollama_host}
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[ERROR] Ollama returned error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("[ERROR] Ollama timeout (120s)")
            return None
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    def parse_llm_response(self, response: str) -> Optional[Dict]:
        """Parse LLM response to extract JSON"""

        try:
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                print("[ERROR] No JSON found in response")
                return None

            json_str = response[start:end]
            memory_data = json.loads(json_str)

            return memory_data

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse error: {e}")
            print(f"[DEBUG] Response: {response[:200]}...")
            return None

    def calculate_age(self, birth_date: str, event_date: str) -> int:
        """Calculate age at time of event"""
        from datetime import datetime

        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        event = datetime.strptime(event_date, "%Y-%m-%d")

        age_days = (event - birth).days
        age_years = age_days // 365

        return age_years

    def generate_kasho_memories(self):
        """Generate all Kasho memories"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Kasho's birth date
        kasho_birth = "2006-05-20"

        # Get all events
        cursor.execute('''
            SELECT event_id, event_date, event_name, description, emotional_impact
            FROM sister_shared_events
            ORDER BY event_id
        ''')

        events = cursor.fetchall()
        total = len(events)

        print(f"\n=== Generating Kasho's Memories ===")
        print(f"Total events: {total}")
        print(f"Kasho's birth: {kasho_birth}\n")

        for i, event_row in enumerate(events, 1):
            event_id = event_row[0]

            event = {
                'event_id': event_row[0],
                'event_date': event_row[1],
                'event_name': event_row[2],
                'description': event_row[3],
                'emotional_impact': event_row[4] if event_row[4] else 5
            }

            # Check if already exists
            cursor.execute("SELECT COUNT(*) FROM kasho_memories WHERE event_id = ?", (event_id,))
            if cursor.fetchone()[0] > 0:
                print(f"[{i}/{total}] Event #{event_id:03d} - SKIP (already exists)")
                continue

            age_years = self.calculate_age(kasho_birth, event['event_date'])

            print(f"[{i}/{total}] Event #{event_id:03d}: {event['event_name']} (Age {age_years})")

            # Generate memory
            prompt = self.generate_kasho_memory_prompt(event, age_years)
            response = self.call_ollama(prompt)

            if not response:
                print(f"  ✗ Failed to generate memory")
                continue

            memory_data = self.parse_llm_response(response)

            if not memory_data:
                print(f"  ✗ Failed to parse response")
                continue

            # Insert into kasho_memories
            cursor.execute('''
                INSERT INTO kasho_memories (
                    event_id, absolute_day, memory_date,
                    kasho_emotion, kasho_action, kasho_thought, diary_entry,
                    botan_observed_behavior, yuri_observed_behavior,
                    botan_inferred_feeling, yuri_inferred_feeling,
                    memory_importance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                (datetime.strptime(event['event_date'], "%Y-%m-%d") - datetime(2006, 5, 20)).days,
                event['event_date'],
                memory_data.get('kasho_emotion'),
                memory_data.get('kasho_action'),
                memory_data.get('kasho_thought'),
                memory_data.get('diary_entry'),
                memory_data.get('botan_observed_behavior'),
                memory_data.get('yuri_observed_behavior'),
                memory_data.get('botan_inferred_feeling'),
                memory_data.get('yuri_inferred_feeling'),
                event['emotional_impact'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            print(f"  ✓ Memory created (Emotion: {memory_data.get('kasho_emotion')})")

        conn.close()
        print(f"\n=== Kasho's memories generation complete ===\n")

    def generate_yuri_memories(self):
        """Generate all Yuri memories (Event 3 onwards)"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Yuri's birth date
        yuri_birth = "2010-07-07"

        # Get events from Yuri's birth onwards (date-based filter)
        cursor.execute('''
            SELECT event_id, event_date, event_name, description, emotional_impact
            FROM sister_shared_events
            WHERE event_date >= ?
            ORDER BY event_id
        ''', (yuri_birth,))

        events = cursor.fetchall()
        total = len(events)

        print(f"\n=== Generating Yuri's Memories ===")
        print(f"Total events: {total}")
        print(f"Yuri's birth: {yuri_birth}\n")

        for i, event_row in enumerate(events, 1):
            event_id = event_row[0]

            event = {
                'event_id': event_row[0],
                'event_date': event_row[1],
                'event_name': event_row[2],
                'description': event_row[3],
                'emotional_impact': event_row[4] if event_row[4] else 5
            }

            # Check if already exists
            cursor.execute("SELECT COUNT(*) FROM yuri_memories WHERE event_id = ?", (event_id,))
            if cursor.fetchone()[0] > 0:
                print(f"[{i}/{total}] Event #{event_id:03d} - SKIP (already exists)")
                continue

            age_years = self.calculate_age(yuri_birth, event['event_date'])

            print(f"[{i}/{total}] Event #{event_id:03d}: {event['event_name']} (Age {age_years})")

            # Generate memory
            prompt = self.generate_yuri_memory_prompt(event, age_years)
            response = self.call_ollama(prompt)

            if not response:
                print(f"  ✗ Failed to generate memory")
                continue

            memory_data = self.parse_llm_response(response)

            if not memory_data:
                print(f"  ✗ Failed to parse response")
                continue

            # Insert into yuri_memories
            cursor.execute('''
                INSERT INTO yuri_memories (
                    event_id, absolute_day, memory_date,
                    yuri_emotion, yuri_action, yuri_thought, diary_entry,
                    kasho_observed_behavior, botan_observed_behavior,
                    kasho_inferred_feeling, botan_inferred_feeling,
                    memory_importance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                (datetime.strptime(event['event_date'], "%Y-%m-%d") - datetime(2010, 7, 7)).days,
                event['event_date'],
                memory_data.get('yuri_emotion'),
                memory_data.get('yuri_action'),
                memory_data.get('yuri_thought'),
                memory_data.get('diary_entry'),
                memory_data.get('kasho_observed_behavior'),
                memory_data.get('botan_observed_behavior'),
                memory_data.get('kasho_inferred_feeling'),
                memory_data.get('botan_inferred_feeling'),
                event['emotional_impact'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            print(f"  ✓ Memory created (Emotion: {memory_data.get('yuri_emotion')})")

        conn.close()
        print(f"\n=== Yuri's memories generation complete ===\n")


if __name__ == "__main__":
    import sys

    generator = SisterMemoryGenerator()

    if len(sys.argv) < 2:
        print("Usage: python3 generate_kasho_yuri_memories.py [kasho|yuri|both]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "kasho":
        generator.generate_kasho_memories()
    elif mode == "yuri":
        generator.generate_yuri_memories()
    elif mode == "both":
        generator.generate_kasho_memories()
        generator.generate_yuri_memories()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python3 generate_kasho_yuri_memories.py [kasho|yuri|both]")
        sys.exit(1)
