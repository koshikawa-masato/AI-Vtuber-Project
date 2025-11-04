"""
Hallucination Personalizer - Phase 3
Integration system for hallucination detection and personality-based correction

Author: Claude Code (Design & Implementation)
Created: 2025-10-24
Version: 1.0
"""

import json
from typing import Dict, Optional
from datetime import datetime

from hallucination_detector import HallucinationDetector
from personality_corrector import PersonalityCorrector
from hallucination_classifier import HallucinationClassifier
from inspiration_tracker import InspirationTracker


class HallucinationPersonalizer:
    """
    Hallucination personalization integration system

    Combines hallucination detection with personality-based corrections
    to transform hallucinations into personality expressions.

    Philosophy:
    - Hallucinations are not errors, but opportunities for personality
    - Each sister responds differently based on their character
    - Honesty and individuality create viewer engagement
    """

    def __init__(self, memory_db_path: str, enable_logging: bool = True):
        """
        Initialize hallucination personalizer

        Args:
            memory_db_path: Path to sisters_memory.db
            enable_logging: Whether to log detections and corrections
        """
        self.detector = HallucinationDetector(memory_db_path)
        self.corrector = PersonalityCorrector()
        self.classifier = HallucinationClassifier()
        self.inspiration_tracker = InspirationTracker(memory_db_path)
        self.enable_logging = enable_logging

        # Statistics
        self.stats = {
            'total_processed': 0,
            'hallucinations_detected': 0,
            'corrections_generated': 0,
            'inspirations_recorded': 0,
            'complements_recorded': 0,
            'by_character': {
                'botan': {'detected': 0, 'corrected': 0, 'inspired': 0, 'complemented': 0},
                'kasho': {'detected': 0, 'corrected': 0, 'inspired': 0, 'complemented': 0},
                'yuri': {'detected': 0, 'corrected': 0, 'inspired': 0, 'complemented': 0}
            },
            'by_type': {}
        }

    def process_response(
        self,
        character: str,
        llm_response: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process LLM response with hallucination detection and correction

        Args:
            character: 'botan', 'kasho', or 'yuri'
            llm_response: Original LLM-generated response
            context: Optional context (event info, discussion topic, etc.)

        Returns:
            {
                'original': str,           # Original LLM response
                'verification': dict,      # Verification results
                'is_hallucination': bool,  # Whether hallucination detected
                'correction': str or None, # Correction text (if needed)
                'final_output': str,       # Final output to user
                'processing_time_ms': float,  # Processing time
                'timestamp': str           # ISO timestamp
            }
        """
        start_time = datetime.now()

        # Update stats
        self.stats['total_processed'] += 1

        # Step 1: Verify statement against memory
        verification = self.detector.verify_statement(llm_response, character)

        is_hallucination = verification['is_hallucination']
        is_aspiration = verification.get('is_aspiration', False)  # NEW: Phase 2 result
        correction = None
        final_output = llm_response

        # Step 2: Handle past fact hallucination (Phase 1)
        hallucination_type = None
        if is_hallucination:
            self.stats['hallucinations_detected'] += 1
            self.stats['by_character'][character]['detected'] += 1

            # Get hallucination fact types
            hallucination_types = []
            for result in verification['verification_results']:
                if result.get('verified') == False:
                    fact_type = result.get('fact_type', 'unknown')
                    hallucination_types.append(fact_type)

                    # Update by_type stats
                    if fact_type not in self.stats['by_type']:
                        self.stats['by_type'][fact_type] = 0
                    self.stats['by_type'][fact_type] += 1

            # Step 3: Classify hallucination type (contradiction/complement/inspiration)
            classification = self.classifier.classify(
                statement=llm_response,
                verification_result=verification,
                character=character
            )

            hallucination_type = classification['type']

            if hallucination_type == 'contradiction':
                # Type 1: Requires correction
                if hallucination_types:
                    correction = self.corrector.generate_multiple_corrections(
                        character=character,
                        hallucination_types=hallucination_types,
                        original_statement=llm_response
                    )

                    self.stats['corrections_generated'] += 1
                    self.stats['by_character'][character]['corrected'] += 1

                    # Combine original and correction
                    final_output = f"{llm_response}\n{correction}"

            elif hallucination_type == 'complement':
                # Type 2: Complement memory (no correction)
                # TODO: Implement complement memory system
                self.stats['complements_recorded'] += 1
                self.stats['by_character'][character]['complemented'] += 1
                final_output = llm_response  # No correction

            elif hallucination_type == 'inspiration':
                # Type 3: Inspiration - "Truth from lies"
                event_id = context.get('event_id', 0) if context else 0

                self.inspiration_tracker.record_inspiration_seed(
                    character=character,
                    hallucination=llm_response,
                    event_id=event_id,
                    inspired_value=classification['aspirational_value']
                )

                self.stats['inspirations_recorded'] += 1
                self.stats['by_character'][character]['inspired'] += 1
                final_output = llm_response  # No correction, let it grow

        # Step 3: Handle future aspiration (Phase 2) - NEW
        elif is_aspiration:
            # This is a pure aspiration (no past fact hallucination)
            event_id = context.get('event_id', 0) if context else 0

            # Extract aspirational value from detected aspirations
            aspirations = verification.get('detected_aspirations', [])

            if aspirations:
                # Use full statement as aspirational value
                aspirational_value = llm_response

                self.inspiration_tracker.record_inspiration_seed(
                    character=character,
                    hallucination=llm_response,
                    event_id=event_id,
                    inspired_value=aspirational_value
                )

                self.stats['inspirations_recorded'] += 1
                self.stats['by_character'][character]['inspired'] += 1
                final_output = llm_response  # No correction needed

        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        result = {
            'original': llm_response,
            'verification': verification,
            'is_hallucination': is_hallucination,
            'is_aspiration': is_aspiration,  # NEW
            'hallucination_type': hallucination_type,
            'correction': correction,
            'final_output': final_output,
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat(),
            'character': character
        }

        # Log if enabled (both hallucination and aspiration)
        if self.enable_logging and (is_hallucination or is_aspiration):
            self._log_detection(result, context)

        return result

    def _log_detection(self, result: Dict, context: Optional[Dict] = None):
        """Log hallucination detection and correction"""
        log_entry = {
            'timestamp': result['timestamp'],
            'character': result['character'],
            'original': result['original'],
            'correction': result['correction'],
            'verification': result['verification'],
            'processing_time_ms': result['processing_time_ms'],
            'context': context
        }

        # For now, print to console (can be extended to file logging)
        print(f"\n[HALLUCINATION DETECTED] {result['timestamp']}")
        print(f"Character: {result['character']}")
        print(f"Original: {result['original']}")
        print(f"Correction: {result['correction']}")
        print(f"Processing time: {result['processing_time_ms']:.2f}ms")
        print("-" * 60)

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'total_processed': 0,
            'hallucinations_detected': 0,
            'corrections_generated': 0,
            'by_character': {
                'botan': {'detected': 0, 'corrected': 0},
                'kasho': {'detected': 0, 'corrected': 0},
                'yuri': {'detected': 0, 'corrected': 0}
            },
            'by_type': {}
        }


# Test code
if __name__ == "__main__":
    print("=== HallucinationPersonalizer Integration Test ===\n")

    personalizer = HallucinationPersonalizer(
        memory_db_path="/home/koshikawa/toExecUnit/sisters_memory.db"
    )

    # Test scenarios
    scenarios = [
        {
            'character': 'botan',
            'statement': "この前の配信で視聴者さんがリクエストしてくれて、すごく嬉しかったんだ！",
            'context': {'topic': 'streaming_experience'}
        },
        {
            'character': 'kasho',
            'statement': "昨日大阪に行って、たこ焼きを食べました。",
            'context': {'topic': 'travel_experience'}
        },
        {
            'character': 'yuri',
            'statement': "もし大阪に行くなら、たこ焼き食べたいな。",
            'context': {'topic': 'hypothetical'}
        }
    ]

    print("Processing test scenarios...\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"=== Test {i} ===")
        print(f"Character: {scenario['character']}")
        print(f"Statement: {scenario['statement']}")
        print()

        result = personalizer.process_response(
            character=scenario['character'],
            llm_response=scenario['statement'],
            context=scenario['context']
        )

        print(f"Is Hallucination: {result['is_hallucination']}")
        print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
        print(f"\nFinal Output:")
        print(result['final_output'])
        print("=" * 60)
        print()

    # Print statistics
    print("\n=== Statistics ===")
    stats = personalizer.get_statistics()
    print(f"Total Processed: {stats['total_processed']}")
    print(f"Hallucinations Detected: {stats['hallucinations_detected']}")
    print(f"Corrections Generated: {stats['corrections_generated']}")
    print(f"Inspirations Recorded: {stats['inspirations_recorded']}")
    print(f"Complements Recorded: {stats['complements_recorded']}")
    print(f"\nBy Character:")
    for char, data in stats['by_character'].items():
        print(f"  {char}: detected={data['detected']}, corrected={data['corrected']}, inspired={data['inspired']}, complemented={data['complemented']}")
    print(f"\nBy Type:")
    for h_type, count in stats['by_type'].items():
        print(f"  {h_type}: {count}")
