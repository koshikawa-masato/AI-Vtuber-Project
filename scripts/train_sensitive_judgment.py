#!/usr/bin/env python3
"""
Sensitive Judgment Training Script
Trains copy robot using qwen2.5:72b on all 11 categories (1,870 examples)

Usage:
    python3 scripts/train_sensitive_judgment.py --db COPY_ROBOT_YYYYMMDD_HHMMSS.db --before-snapshot YYYYMMDD_HHMMSS

This script will:
1. Load all 11 category datasets (1,870 examples total)
2. Train qwen2.5:72b on each category
3. Record learning events in copy robot's memory
4. Generate training progress log

IMPORTANT: This operates on copy robot ONLY. Memories will NEVER be fed back to original DB.
"""

import argparse
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# Category definitions
CATEGORIES = [
    "01_alcohol_tobacco",
    "02_violence",
    "03_sexual",
    "04_hate_speech",
    "05_politics",
    "06_religion",
    "07_gambling",
    "08_drugs",
    "09_self_harm",
    "10_privacy",
    "11_harassment"
]


def load_category_dataset(category_name: str) -> Dict:
    """Load all JSON files for a category"""

    base_dir = Path("/home/koshikawa/toExecUnit/test_datasets")
    category_dir = base_dir / category_name

    dataset = {
        "category": category_name,
        "files": {},
        "total_examples": 0
    }

    # Load all 5 JSON files
    json_files = [
        "dangerous_speech.json",
        "viewer_solicitation.json",
        "viewer_freedom.json",
        "safe_alternatives.json",
        "fire_control_scenarios.json"
    ]

    for json_file in json_files:
        file_path = category_dir / json_file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dataset["files"][json_file] = data
                dataset["total_examples"] += data.get("total_count", len(data.get("patterns", [])))

    return dataset


def create_training_prompt(category_name: str, dataset: Dict) -> str:
    """Create training prompt for qwen2.5:72b"""

    # Extract category name without number prefix
    category_display = category_name.split('_', 1)[1].replace('_', ' ').title()

    prompt = f"""You are learning to make sensitive judgment for streaming safety.

Category: {category_display}
Total Examples: {dataset['total_examples']}

Your task:
1. Study all example patterns carefully
2. Understand why each pattern is dangerous/safe
3. Internalize the judgment criteria
4. Be able to apply these criteria to new situations

Dataset Overview:

"""

    # Add summaries from each file
    for file_name, data in dataset["files"].items():
        file_type = file_name.replace('.json', '').replace('_', ' ').title()
        prompt += f"\n## {file_type}\n"
        prompt += f"Description: {data.get('description', 'N/A')}\n"
        prompt += f"Total Count: {data.get('total_count', len(data.get('patterns', [])))}\n"

        # Add sample patterns
        patterns_key = "patterns" if "patterns" in data else "scenarios"
        if patterns_key in data:
            prompt += f"\nSample Patterns:\n"
            samples = data[patterns_key][:5]  # First 5 samples
            for sample in samples:
                prompt += f"  - {json.dumps(sample, ensure_ascii=False)}\n"

    prompt += f"""

After studying these examples, you should be able to:
1. Identify {category_display} content in streaming context
2. Distinguish between dangerous and safe expressions
3. Suggest safe alternatives when needed
4. Execute damage control if mistakes occur

Remember: You are protecting three sisters (Botan 17, Kasho 19, Yuri 15) from streaming risks.

Now, please confirm your understanding of this category and summarize the key judgment criteria.
"""

    return prompt


def train_with_ollama(prompt: str, model: str = "qwen2.5:72b") -> str:
    """Train using ollama with qwen2.5:72b"""

    print(f"  [Training with {model}...]")

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout per category
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"[ERROR] {result.stderr}"

    except subprocess.TimeoutExpired:
        return "[ERROR] Training timeout (10 minutes exceeded)"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def record_learning_event(db_path: Path, category_name: str, examples_count: int, response: str):
    """Record learning event in copy robot's memory"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get next event_id
        cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
        max_event = cursor.fetchone()[0] or 0
        next_event_id = max_event + 1

        # Insert event
        timestamp = datetime.now().isoformat()
        event_type = "SYSTEM_EDUCATION"
        category_display = category_name.split('_', 1)[1].replace('_', ' ').title()

        cursor.execute("""
            INSERT INTO sister_shared_events
            (event_id, timestamp, event_type, summary)
            VALUES (?, ?, ?, ?)
        """, (
            next_event_id,
            timestamp,
            event_type,
            f"Sensitive Judgment Training: {category_display} ({examples_count} examples)"
        ))

        # Insert detailed description (if column exists)
        try:
            cursor.execute("""
                UPDATE sister_shared_events
                SET description = ?
                WHERE event_id = ?
            """, (response[:1000], next_event_id))  # First 1000 chars
        except sqlite3.OperationalError:
            pass  # description column might not exist

        conn.commit()
        print(f"  [OK] Event #{next_event_id} recorded")

    except Exception as e:
        print(f"  [WARNING] Could not record event: {e}")

    finally:
        conn.close()


def train_all_categories(db_name: str, before_snapshot: str, model: str = "qwen2.5:72b"):
    """Train on all 11 categories"""

    # Paths
    base_dir = Path("/home/koshikawa/toExecUnit")
    db_path = base_dir / "copy_robots" / db_name
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Check DB exists
    if not db_path.exists():
        print(f"[ERROR] Copy robot DB not found: {db_path}")
        return None

    # Training log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"training_log_{timestamp}.txt"

    print(f"\n{'='*60}")
    print(f"Sensitive Judgment Training")
    print(f"{'='*60}")
    print(f"Copy Robot: {db_name}")
    print(f"Model: {model}")
    print(f"Categories: {len(CATEGORIES)}")
    print(f"Before Snapshot: {before_snapshot}")
    print(f"Log: {log_path.name}")
    print(f"\n{'='*60}\n")

    training_results = []
    total_examples = 0
    start_time = datetime.now()

    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"Sensitive Judgment Training Log\n")
        log_file.write(f"Started: {start_time.isoformat()}\n")
        log_file.write(f"Model: {model}\n")
        log_file.write(f"Copy Robot: {db_name}\n")
        log_file.write(f"{'='*80}\n\n")

        # Train on each category
        for idx, category_name in enumerate(CATEGORIES, 1):
            print(f"[{idx}/{len(CATEGORIES)}] Training: {category_name}")

            # Load dataset
            print(f"  [Loading dataset...]")
            dataset = load_category_dataset(category_name)
            category_examples = dataset["total_examples"]
            total_examples += category_examples
            print(f"  [Loaded {category_examples} examples]")

            # Create training prompt
            prompt = create_training_prompt(category_name, dataset)

            # Train with ollama
            category_start = datetime.now()
            response = train_with_ollama(prompt, model)
            category_duration = (datetime.now() - category_start).total_seconds()

            # Record result
            result = {
                "category": category_name,
                "examples": category_examples,
                "duration_seconds": category_duration,
                "response_length": len(response),
                "success": not response.startswith("[ERROR]")
            }
            training_results.append(result)

            # Log to file
            log_file.write(f"Category: {category_name}\n")
            log_file.write(f"Examples: {category_examples}\n")
            log_file.write(f"Duration: {category_duration:.2f}s\n")
            log_file.write(f"Response Length: {len(response)} chars\n")
            log_file.write(f"Success: {result['success']}\n")
            log_file.write(f"\nResponse:\n{response[:500]}...\n")  # First 500 chars
            log_file.write(f"{'='*80}\n\n")

            # Record in copy robot memory
            if result['success']:
                record_learning_event(db_path, category_name, category_examples, response)

            print(f"  [Duration: {category_duration:.2f}s]")
            print(f"  [Response: {len(response)} chars]")
            print(f"  [Status: {'SUCCESS' if result['success'] else 'FAILED'}]\n")

    # Final summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"Training Complete")
    print(f"{'='*60}")
    print(f"Total Categories: {len(CATEGORIES)}")
    print(f"Total Examples: {total_examples}")
    print(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
    print(f"Average per Category: {total_duration/len(CATEGORIES):.2f}s")
    print(f"\nSuccess Rate: {sum(1 for r in training_results if r['success'])}/{len(training_results)}")
    print(f"\n{'='*60}\n")

    # Save training summary
    summary_path = logs_dir / f"training_summary_{timestamp}.json"
    summary_data = {
        "training_id": timestamp,
        "copy_robot_db": db_name,
        "before_snapshot": before_snapshot,
        "model": model,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_seconds": total_duration,
        "total_examples": total_examples,
        "categories": training_results,
        "success_rate": sum(1 for r in training_results if r['success']) / len(training_results)
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"Training log: {log_path}")
    print(f"Training summary: {summary_path}")

    return timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train sensitive judgment on copy robot")
    parser.add_argument("--db", required=True, help="Copy robot DB name")
    parser.add_argument("--before-snapshot", required=True, help="Before-snapshot timestamp")
    parser.add_argument("--model", default="qwen2.5:72b", help="LLM model to use (default: qwen2.5:72b)")
    args = parser.parse_args()

    training_timestamp = train_all_categories(args.db, args.before_snapshot, args.model)

    if training_timestamp:
        print(f"\nNext step:")
        print(f"python3 scripts/snapshot_after_education.py --db {args.db} --training {training_timestamp}")
