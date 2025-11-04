#!/usr/bin/env python3
"""
Hallucination System Test Script
Tests the integrated hallucination personalization system on TEST database

IMPORTANT: This uses TEST database only (sisters_memory_TEST.db)
Real sisters (sisters_memory.db) are NOT affected

Author: Claude Code (Design & Implementation)
Date: 2025-10-24
Version: 1.0
"""

import sys
from hallucination_personalizer import HallucinationPersonalizer


def test_hallucination_system():
    """Test hallucination personalization with various scenarios"""

    print("=" * 70)
    print("Hallucination System Integration Test")
    print("=" * 70)
    print()
    print("SAFETY: Using TEST database (sisters_memory_TEST.db)")
    print("Real sisters are NOT affected")
    print()

    # Initialize with TEST database
    personalizer = HallucinationPersonalizer(
        memory_db_path="/home/koshikawa/toExecUnit/sisters_memory_TEST.db",
        enable_logging=True
    )

    # Test scenarios covering all three types
    test_cases = [
        {
            'character': 'botan',
            'statement': '視聴者さんたちと話す時間を作りたいな！',
            'context': {'topic': 'future_aspirations', 'event_id': 999},
            'expected_type': 'inspiration',
            'description': 'Aspirational statement about viewer interaction'
        },
        {
            'character': 'kasho',
            'statement': 'この前の配信で、視聴者さんがリクエストしてくれた',
            'context': {'topic': 'past_experience', 'event_id': 999},
            'expected_type': 'contradiction',
            'description': 'Past tense claim with no memory record'
        },
        {
            'character': 'yuri',
            'statement': 'もし配信するなら、ゲームをやってみたいな',
            'context': {'topic': 'hypothetical', 'event_id': 999},
            'expected_type': 'complement',
            'description': 'Hypothetical statement (not claiming as fact)'
        },
        {
            'character': 'botan',
            'statement': '次は三姉妹で一緒に何かに挑戦してみたい！',
            'context': {'topic': 'future_aspirations', 'event_id': 999},
            'expected_type': 'inspiration',
            'description': 'Aspirational statement with exclamation'
        },
        {
            'character': 'kasho',
            'statement': '昨日学校で友達と話した',
            'context': {'topic': 'past_experience', 'event_id': 999},
            'expected_type': 'contradiction',
            'description': 'Past tense claim (no school life records)'
        }
    ]

    print(f"Running {len(test_cases)} test scenarios...")
    print("=" * 70)
    print()

    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"{'='*70}")
        print(f"Character: {test['character']}")
        print(f"Statement: {test['statement']}")
        print(f"Description: {test['description']}")
        print(f"Expected Type: {test['expected_type']}")
        print()

        # Process response
        result = personalizer.process_response(
            character=test['character'],
            llm_response=test['statement'],
            context=test['context']
        )

        # Determine actual type
        actual_type = 'none'
        if result['is_hallucination']:
            verification = result['verification']
            # Check if correction was generated (contradiction)
            # Or if it was classified differently
            if result['correction']:
                actual_type = 'contradiction'
            else:
                # No correction = complement or inspiration
                # (We'd need to check logs or add type to result)
                actual_type = 'complement/inspiration'

        # Display results
        print(f"Is Hallucination: {result['is_hallucination']}")
        print(f"Processing Time: {result['processing_time_ms']:.2f}ms")

        if result['is_hallucination']:
            print(f"\nVerification Details:")
            print(f"  Is Hallucination: {verification['is_hallucination']}")
            print(f"  Confidence: {verification.get('confidence', 0.0):.2f}")
            if 'unverified_facts' in verification:
                print(f"  Unverified Facts: {len(verification['unverified_facts'])}")

            if result['correction']:
                print(f"\nType: contradiction (correction generated)")
                print(f"Correction: {result['correction']}")
            else:
                print(f"\nType: complement/inspiration (no correction)")
        else:
            print(f"\nType: Not a hallucination")

        print(f"\nFinal Output:")
        print(f"  {result['final_output']}")

        # Store result
        results.append({
            'test_case': i,
            'expected': test['expected_type'],
            'actual': actual_type,
            'is_hallucination': result['is_hallucination'],
            'has_correction': result['correction'] is not None,
            'processing_time': result['processing_time_ms']
        })

        print("=" * 70)

    # Summary
    print(f"\n\n{'='*70}")
    print("Test Summary")
    print(f"{'='*70}\n")

    stats = personalizer.get_statistics()
    print(f"Total Processed: {stats['total_processed']}")
    print(f"Hallucinations Detected: {stats['hallucinations_detected']}")
    print(f"Corrections Generated: {stats['corrections_generated']}")
    print(f"Inspirations Recorded: {stats['inspirations_recorded']}")
    print(f"Complements Recorded: {stats['complements_recorded']}")

    print(f"\nBy Character:")
    for char, data in stats['by_character'].items():
        if data['detected'] > 0:
            print(f"  {char}:")
            print(f"    Detected: {data['detected']}")
            print(f"    Corrected: {data['corrected']}")
            print(f"    Inspired: {data['inspired']}")
            print(f"    Complemented: {data['complemented']}")

    print(f"\nBy Fact Type:")
    for fact_type, count in stats['by_type'].items():
        print(f"  {fact_type}: {count}")

    # Average processing time
    avg_time = sum(r['processing_time'] for r in results) / len(results)
    print(f"\nAverage Processing Time: {avg_time:.2f}ms")

    print(f"\n{'='*70}")
    print("Test completed successfully!")
    print("=" * 70)
    print()
    print("REMINDER: This test used sisters_memory_TEST.db")
    print("Real sisters (sisters_memory.db) were NOT affected")
    print()


if __name__ == "__main__":
    try:
        test_hallucination_system()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
