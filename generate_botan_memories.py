#!/usr/bin/env python3
"""
Phase 1.5: Botan Memory Generation Script
Generates Botan's subjective memories from objective events
Uses LLM to create age-appropriate emotional responses
"""

import sqlite3
import json
import subprocess
import os
from datetime import datetime
from typing import Dict, Optional

class BotanMemoryGenerator:
    """Generate Botan's subjective memories from objective events"""

    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db"):
        self.db_path = db_path
        self.ollama_host = "http://localhost:11434"

    def get_character_context(self, age_years: int) -> str:
        """Get Botan's character traits based on age"""

        if age_years == 0:
            return "Newborn baby. No conscious thoughts yet."
        elif 1 <= age_years <= 2:
            return "Toddler. Simple emotions: happy, sad, scared. No complex thoughts."
        elif 3 <= age_years <= 5:
            return "Early childhood in LA. Learning English and Japanese. Confused but curious."
        elif 6 <= age_years <= 10:
            return "LA period. Bilingual child. Struggling with identity (Japanese? American?). Close to sisters."
        elif 11 <= age_years <= 14:
            return "Back in Japan. Becoming gyaru. Starting to use gyaru slang. Finding herself."
        elif 15 <= age_years <= 17:
            return "Current age. Full gyaru mode. VTuber fan. Tech-curious but not expert. Confident and expressive."
        else:
            return "Unknown age"

    def generate_memory_prompt(self, event: Dict, age_years: int) -> str:
        """Generate prompt for LLM to create Botan's subjective memory"""

        character_context = self.get_character_context(age_years)

        prompt = f"""You are Botan (牡丹), a 17-year-old gyaru high school girl. You are recalling a memory from when you were {age_years} years old.

**Character Context (Age {age_years})**: {character_context}

**Objective Event**:
- Event: {event['event_name']}
- Date: {event['event_date']}
- What happened: {event['description']}
- Your age: {age_years} years old
- Emotional impact: {event['emotional_impact']}/10

**Your task**: Generate your SUBJECTIVE memory of this event. This is YOUR perspective, YOUR feelings, YOUR thoughts.

**Output JSON format**:
{{
    "botan_emotion": "Your emotion at that time (joy, sadness, fear, confusion, excitement, etc.)",
    "botan_action": "What YOU did (crying, laughing, asking questions, running away, etc.)",
    "botan_thought": "What YOU thought (age-appropriate - simple if young, complex if older)",
    "diary_entry": "If you were to write a diary entry about this (age-appropriate language)",
    "kasho_observed_behavior": "What you SAW Kasho do (observable actions only)",
    "yuri_observed_behavior": "What you SAW Yuri do (observable actions only, null if Yuri not born yet)",
    "kasho_inferred_feeling": "What you GUESS Kasho felt (start with '多分' or 'Maybe')",
    "yuri_inferred_feeling": "What you GUESS Yuri felt (start with '多分' or 'Maybe', null if Yuri not born yet)"
}}

**Important rules**:
1. Use age-appropriate language and thoughts
2. Age 0-2: Very simple emotions, no complex thoughts
3. Age 3-10: Mix Japanese and English if in LA
4. Age 11+: Use gyaru slang (マジで、ヤバい、〜じゃん)
5. You can OBSERVE what sisters do, but you can only GUESS what they feel
6. Be honest about your feelings - even negative ones
7. Return ONLY valid JSON, no other text

Generate the JSON now:"""

        return prompt

    def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM to generate memory"""

        try:
            # Use ollama CLI
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
            # Try to find JSON in response
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

    def memory_exists(self, event_id: int) -> bool:
        """Check if memory already exists for this event"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM botan_memories WHERE event_id = ?", (event_id,))
        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def insert_botan_memory(self, event_id: int, event: Dict, memory_data: Dict):
        """Insert Botan's memory into botan_memories table"""

        # Check if memory already exists
        if self.memory_exists(event_id):
            print(f"[SKIP] Memory for Event #{event['event_number']:03d} already exists")
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO botan_memories (
                    event_id, absolute_day, memory_date,
                    botan_emotion, botan_action, botan_thought, diary_entry,
                    kasho_observed_behavior, yuri_observed_behavior,
                    kasho_inferred_feeling, yuri_inferred_feeling,
                    memory_importance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event['botan_absolute_day'],
                event['event_date'],
                memory_data.get('botan_emotion'),
                memory_data.get('botan_action'),
                memory_data.get('botan_thought'),
                memory_data.get('diary_entry'),
                memory_data.get('kasho_observed_behavior'),
                memory_data.get('yuri_observed_behavior'),
                memory_data.get('kasho_inferred_feeling'),
                memory_data.get('yuri_inferred_feeling'),
                event['emotional_impact']  # Use same impact as objective event
            ))

            conn.commit()
            print(f"[SUCCESS] Inserted memory for Event #{event['event_number']:03d}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to insert memory: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def generate_all_memories(self, start_event: int = 2, end_event: int = 100):
        """Generate all Botan memories from events"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all events where Botan participated
        cursor.execute("""
            SELECT * FROM sister_shared_events
            WHERE botan_absolute_day IS NOT NULL
            AND event_number BETWEEN ? AND ?
            ORDER BY botan_absolute_day
        """, (start_event, end_event))

        events = cursor.fetchall()
        conn.close()

        print(f"[INFO] Generating memories for {len(events)} events...")
        print(f"[INFO] This may take a while (estimated {len(events) * 2} minutes)")

        success_count = 0
        skip_count = 0
        fail_count = 0

        for row in events:
            event = dict(row)
            event_num = event['event_number']
            age = event['botan_age_years']

            print(f"\n{'='*60}")
            print(f"Event #{event_num:03d}: {event['event_name']}")
            print(f"Botan age: {age} years, Impact: {event['emotional_impact']}/10")
            print(f"{'='*60}")

            # Check if already exists
            if self.memory_exists(event['event_id']):
                print(f"[SKIP] Memory already exists")
                skip_count += 1
                print(f"[INFO] Progress: {success_count + skip_count + fail_count}/{len(events)} (Success: {success_count}, Skip: {skip_count}, Fail: {fail_count})")
                continue

            # Generate prompt
            prompt = self.generate_memory_prompt(event, age)

            # Call LLM
            print(f"[INFO] Calling Ollama (qwen2.5:32b)...")
            response = self.call_ollama(prompt)

            if not response:
                print(f"[FAIL] Event #{event_num:03d}: No response from LLM")
                fail_count += 1
                continue

            # Parse response
            memory_data = self.parse_llm_response(response)

            if not memory_data:
                print(f"[FAIL] Event #{event_num:03d}: Failed to parse response")
                fail_count += 1
                continue

            # Insert into database
            result = self.insert_botan_memory(event['event_id'], event, memory_data)
            if result:
                success_count += 1
            else:
                fail_count += 1

            print(f"[INFO] Progress: {success_count + skip_count + fail_count}/{len(events)} (Success: {success_count}, Skip: {skip_count}, Fail: {fail_count})")

        print(f"\n{'='*60}")
        print(f"[COMPLETE] Memory generation finished")
        print(f"[SUCCESS] {success_count} memories created")
        print(f"[SKIP] {skip_count} memories already existed")
        print(f"[FAIL] {fail_count} memories failed")
        print(f"[TOTAL] {success_count + skip_count}/{len(events)} memories in database")
        print(f"{'='*60}")


def main():
    """Main function"""

    print("="*60)
    print("Phase 1.5: Botan Memory Generation")
    print("="*60)

    generator = BotanMemoryGenerator()

    # Generate all memories (Event 002-100)
    # Event 001 is before Botan was born
    generator.generate_all_memories(start_event=2, end_event=100)


if __name__ == "__main__":
    main()
