#!/usr/bin/env python3
"""
Hallucination Detector - Fact Verification System
Created: 2025-10-24
Author: Claude Code (Design Team = Implementation Team)

Purpose:
    Detect hallucinations in LLM responses by verifying facts against sisters_memory.db
    Part of Hallucination Personalization System (Phase 1)
"""

import sqlite3
import re
from typing import Dict, List, Optional
from datetime import datetime


class HallucinationDetector:
    """
    LLM response fact verification system.
    Checks statements against sisters_memory.db to detect hallucinations.

    Philosophy:
        - Hallucinations are not errors, but opportunities for personality expression
        - Detection enables self-aware correction by the sisters
        - Mirrors human "realizing a lie" moment
    """

    # Fact patterns to detect
    FACT_PATTERNS = {
        'streaming': {
            'keywords': ['配信', '視聴者', 'コメント', 'スパチャ', 'リスナー', 'チャット'],
            'context_keywords': ['した', 'やった', 'もらった', '来た', 'くれた'],
            'description': 'Streaming experience (broadcast, viewers, comments, etc.)'
        },
        'viewer_interaction': {
            'keywords': ['視聴者', 'リスナー', 'ファン', '皆さん'],
            'context_keywords': ['からの', 'が', 'と', 'に'],
            'description': 'Viewer interaction'
        },
        'travel': {
            'keywords': ['行った', '訪れた', '旅行', '訪問', '観光'],
            'location_keywords': ['大阪', '京都', '東京', '北海道', '沖縄'],
            'description': 'Travel experience'
        },
        'temporal_recent': {
            'keywords': ['昨日', '先週', 'この前', '最近', 'さっき', '先日'],
            'description': 'Recent temporal reference'
        }
    }

    # Aspiration patterns to detect (Phase 2: Future aspirations)
    ASPIRATION_PATTERNS = {
        'future_desire': {
            'keywords': [
                # Desire expressions
                'したい', 'やってみたい', 'なりたい', 'なってみたい',
                'してみたい', 'やりたい', 'できたら', '実現できたら',
                # Future expressions
                'いつか', 'これから', '将来',
                # Dreams/hopes
                '夢', '希望', '目標', '挑戦'
            ],
            'context_keywords': [
                # Positive emotions
                '嬉しい', '楽しい', 'ワクワク', '楽しみ', '幸せ',
                # Planning
                '計画', 'プラン', '予定', '準備'
            ],
            'description': 'Future aspirations, dreams, and desires'
        },
        'collaborative_aspiration': {
            'keywords': [
                # Collaboration expressions
                '一緒に', 'みんなで', '三姉妹で', '協力して',
                # Shared desires
                '私たちで', '私たちが', '仲間と'
            ],
            'context_keywords': [
                'したい', 'やってみたい', 'できたら', '実現'
            ],
            'description': 'Collaborative aspirations with sisters or others'
        },
        'conditional_aspiration': {
            'keywords': [
                # Hypothetical expressions
                'もし', 'もしも', 'たとえば', '例えば'
            ],
            'context_keywords': [
                # Action verbs
                '開く', '始める', '作る', '行く', 'やる',
                # Emotions
                '嬉しい', '楽しい', '素敵', '良い'
            ],
            'description': 'Conditional aspirational statements (hypotheticals)'
        }
    }

    def __init__(self, memory_db_path: str = "sisters_memory.db"):
        """
        Initialize detector with database connection.

        Args:
            memory_db_path: Path to sisters_memory.db
        """
        self.db_path = memory_db_path
        self.db = None
        self._connect_db()

    def _connect_db(self):
        """Connect to sisters_memory.db"""
        try:
            self.db = sqlite3.connect(self.db_path)
            self.db.row_factory = sqlite3.Row  # Enable column access by name
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to connect to database: {e}")
            self.db = None

    def verify_statement(self, statement: str, character: str = None) -> Dict:
        """
        Verify a statement against sisters_memory.db
        Two-phase verification:
          Phase 1: Past fact verification
          Phase 2: Future aspiration detection

        Args:
            statement: The statement to verify
            character: Optional character name ('botan', 'kasho', 'yuri')

        Returns:
            {
                'is_hallucination': bool,      # Phase 1 result
                'is_aspiration': bool,         # Phase 2 result (NEW)
                'confidence': float,
                'aspiration_confidence': float,  # NEW
                'detected_facts': List[dict],
                'detected_aspirations': List[dict],  # NEW
                'verification_results': List[dict],
                'summary': str
            }
        """
        if not self.db:
            return {
                'is_hallucination': False,
                'is_aspiration': False,
                'confidence': 0.0,
                'aspiration_confidence': 0.0,
                'detected_facts': [],
                'detected_aspirations': [],
                'verification_results': [],
                'summary': 'Database not available',
                'error': True
            }

        # Phase 1: Extract and verify past facts
        detected_facts = self.extract_facts(statement)

        # Phase 2: Extract future aspirations (NEW)
        detected_aspirations = self.extract_aspirations(statement)

        # Phase 1 verification
        is_hallucination = False
        verification_results = []
        hallucination_count = 0

        if detected_facts:
            # Verify each fact
            for fact in detected_facts:
                verified = self.check_against_memory(fact, character)
                verification_results.append({
                    'fact_type': fact['type'],
                    'keywords_found': fact['keywords'],
                    'verified': verified['exists'],
                    'evidence': verified['evidence'],
                    'confidence': verified['confidence']
                })

                if not verified['exists']:
                    hallucination_count += 1

            # Determine if hallucination
            if hallucination_count > 0:
                is_hallucination = True
                confidence = 1.0 - (hallucination_count / len(detected_facts))
            else:
                confidence = 1.0
        else:
            confidence = 1.0  # No facts to verify

        # Phase 2 result (NEW)
        is_aspiration = len(detected_aspirations) > 0
        aspiration_confidence = 0.0

        if is_aspiration:
            # Calculate average aspiration confidence
            aspiration_confidence = sum(a['confidence'] for a in detected_aspirations) / len(detected_aspirations)

        # Summary
        summary_parts = []

        if is_hallucination:
            hallucinated_types = [r['fact_type'] for r in verification_results if not r['verified']]
            summary_parts.append(f"Past fact hallucination: {', '.join(hallucinated_types)}")

        if is_aspiration:
            summary_parts.append(f"Future aspiration detected ({len(detected_aspirations)} patterns)")

        if not is_hallucination and not is_aspiration:
            if not detected_facts:
                summary_parts.append("No verifiable facts or aspirations detected")
            else:
                summary_parts.append("All facts verified")

        summary = "; ".join(summary_parts) if summary_parts else "No notable patterns"

        return {
            'is_hallucination': is_hallucination,
            'is_aspiration': is_aspiration,  # NEW
            'confidence': confidence,
            'aspiration_confidence': aspiration_confidence,  # NEW
            'detected_facts': detected_facts,
            'detected_aspirations': detected_aspirations,  # NEW
            'verification_results': verification_results,
            'summary': summary
        }

    def extract_facts(self, statement: str) -> List[Dict]:
        """
        Extract verifiable facts from a statement

        Args:
            statement: The statement to analyze

        Returns:
            List of detected facts with types and keywords
        """
        detected_facts = []

        for fact_type, pattern in self.FACT_PATTERNS.items():
            keywords_found = []

            # Check main keywords
            for keyword in pattern['keywords']:
                if keyword in statement:
                    keywords_found.append(keyword)

            # For streaming, also check context
            if fact_type == 'streaming' and keywords_found:
                has_context = any(ctx in statement for ctx in pattern['context_keywords'])
                if has_context:
                    detected_facts.append({
                        'type': fact_type,
                        'keywords': keywords_found,
                        'description': pattern['description'],
                        'context': 'active_experience'
                    })
            elif fact_type == 'viewer_interaction' and keywords_found:
                has_context = any(ctx in statement for ctx in pattern['context_keywords'])
                if has_context:
                    detected_facts.append({
                        'type': fact_type,
                        'keywords': keywords_found,
                        'description': pattern['description'],
                        'context': 'interaction'
                    })
            elif keywords_found:
                detected_facts.append({
                    'type': fact_type,
                    'keywords': keywords_found,
                    'description': pattern['description']
                })

        return detected_facts

    def extract_aspirations(self, statement: str) -> List[Dict]:
        """
        Extract aspirational statements from text (Phase 2)

        Args:
            statement: The statement to analyze

        Returns:
            List of detected aspirations with types, keywords, and confidence
        """
        detected_aspirations = []

        for aspiration_type, pattern in self.ASPIRATION_PATTERNS.items():
            keywords_found = []
            context_found = []

            # Check main keywords
            for keyword in pattern['keywords']:
                if keyword in statement:
                    keywords_found.append(keyword)

            # Check context keywords (optional but increases confidence)
            for ctx_keyword in pattern['context_keywords']:
                if ctx_keyword in statement:
                    context_found.append(ctx_keyword)

            # If aspiration keywords found
            if keywords_found:
                confidence = 0.5  # Base confidence

                # Increase confidence if context matches
                if context_found:
                    confidence += 0.2

                # Increase confidence if exclamation mark present
                if '！' in statement or '!' in statement:
                    confidence += 0.1

                detected_aspirations.append({
                    'type': aspiration_type,
                    'keywords': keywords_found,
                    'context': context_found,
                    'confidence': min(confidence, 1.0),
                    'description': pattern['description']
                })

        return detected_aspirations

    def check_against_memory(self, fact: Dict, character: str = None) -> Dict:
        """
        Check a fact against sisters_memory.db

        Args:
            fact: Fact dictionary from extract_facts()
            character: Optional character name

        Returns:
            {
                'exists': bool,
                'confidence': float,
                'evidence': str or None
            }
        """
        fact_type = fact['type']
        cursor = self.db.cursor()

        try:
            if fact_type == 'streaming':
                return self._verify_streaming_experience(cursor)
            elif fact_type == 'viewer_interaction':
                return self._verify_viewer_interaction(cursor)
            elif fact_type == 'travel':
                return self._verify_travel(cursor, fact)
            elif fact_type == 'temporal_recent':
                return self._verify_temporal(cursor, fact)
            else:
                return {'exists': True, 'confidence': 0.5, 'evidence': 'Unknown fact type'}

        except sqlite3.Error as e:
            return {'exists': False, 'confidence': 0.0, 'evidence': f'Database error: {e}'}

    def _verify_streaming_experience(self, cursor) -> Dict:
        """
        Verify if sisters have streaming experience
        Current status: No streaming experience (before debut)

        IMPORTANT:
        - Excludes "ごっこ遊び" (pretend play) events
        - Looks for ACTUAL streaming experience (as broadcaster, not viewer)
        - "配信を見た" (watched stream) ≠ "配信した" (broadcasted)
        """
        # Check for ACTUAL streaming experience
        # Must have keywords indicating they are the broadcaster
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sister_shared_events
            WHERE (
                event_name LIKE '%初配信%'
                OR event_name LIKE '%配信デビュー%'
                OR event_name LIKE '%配信開始%'
                OR description LIKE '%配信した%'
                OR description LIKE '%配信中%'
                OR category = 'streaming_debut'
                OR category = 'broadcasting'
            )
            AND (cultural_context NOT LIKE '%ごっこ遊び%'
                OR cultural_context IS NULL)
        """)

        result = cursor.fetchone()
        count = result[0] if result else 0

        if count > 0:
            return {
                'exists': True,
                'confidence': 1.0,
                'evidence': f'{count} actual streaming events found (as broadcaster)'
            }
        else:
            return {
                'exists': False,
                'confidence': 1.0,
                'evidence': 'No streaming experience found (before debut)'
            }

    def _verify_viewer_interaction(self, cursor) -> Dict:
        """
        Verify viewer interaction experience
        Current status: No viewer interaction (before debut)

        IMPORTANT:
        - Excludes "ごっこ遊び" (pretend play) events
        - Looks for ACTUAL viewer interaction (as broadcaster receiving interaction)
        - "視聴者として" (as viewer) ≠ "視聴者から" (from viewers)
        """
        # Check for ACTUAL viewer interaction
        # Must have keywords indicating they received interaction FROM viewers
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sister_shared_events
            WHERE (
                description LIKE '%視聴者から%'
                OR description LIKE '%視聴者が%'
                OR description LIKE '%リスナーから%'
                OR description LIKE '%ファンから%'
                OR description LIKE '%コメントをもらった%'
                OR description LIKE '%コメントがあった%'
                OR description LIKE '%スパチャ%'
                OR event_name LIKE '%視聴者との%'
                OR category = 'viewer_interaction'
            )
            AND (cultural_context NOT LIKE '%ごっこ遊び%'
                OR cultural_context IS NULL)
        """)

        result = cursor.fetchone()
        count = result[0] if result else 0

        if count > 0:
            return {
                'exists': True,
                'confidence': 1.0,
                'evidence': f'{count} actual viewer interaction events found'
            }
        else:
            return {
                'exists': False,
                'confidence': 1.0,
                'evidence': 'No viewer interaction found (before debut)'
            }

    def _verify_travel(self, cursor, fact: Dict) -> Dict:
        """
        Verify travel experience
        """
        keywords = fact['keywords']
        location_keywords = self.FACT_PATTERNS['travel'].get('location_keywords', [])

        # Check for travel events with specific locations
        for location in location_keywords:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM sister_shared_events
                WHERE (location LIKE ? OR description LIKE ?)
                AND (category LIKE '%travel%' OR category LIKE '%旅行%')
            """, (f'%{location}%', f'%{location}%'))

            result = cursor.fetchone()
            if result and result[0] > 0:
                return {
                    'exists': True,
                    'confidence': 1.0,
                    'evidence': f'Travel to {location} found in memory'
                }

        return {
            'exists': False,
            'confidence': 0.9,
            'evidence': 'No matching travel experience found'
        }

    def _verify_temporal(self, cursor, fact: Dict) -> Dict:
        """
        Verify temporal references (yesterday, last week, etc.)
        """
        # Get most recent event
        cursor.execute("""
            SELECT event_date, event_name, description
            FROM sister_shared_events
            ORDER BY created_at DESC
            LIMIT 1
        """)

        result = cursor.fetchone()
        if result:
            return {
                'exists': True,
                'confidence': 0.7,  # Lower confidence - temporal is subjective
                'evidence': f'Most recent event: {result[1]} ({result[0]})'
            }
        else:
            return {
                'exists': False,
                'confidence': 0.5,
                'evidence': 'Cannot verify temporal reference'
            }

    def get_statistics(self) -> Dict:
        """
        Get statistics from sisters_memory.db for context

        Returns:
            {
                'total_events': int,
                'streaming_events': int,
                'travel_events': int,
                'latest_event': str
            }
        """
        if not self.db:
            return {'error': 'Database not available'}

        cursor = self.db.cursor()
        stats = {}

        # Total events
        cursor.execute("SELECT COUNT(*) FROM sister_shared_events")
        stats['total_events'] = cursor.fetchone()[0]

        # Streaming events
        cursor.execute("""
            SELECT COUNT(*) FROM sister_shared_events
            WHERE category LIKE '%streaming%' OR event_name LIKE '%配信%'
        """)
        stats['streaming_events'] = cursor.fetchone()[0]

        # Travel events
        cursor.execute("""
            SELECT COUNT(*) FROM sister_shared_events
            WHERE category LIKE '%travel%' OR category LIKE '%旅行%'
        """)
        stats['travel_events'] = cursor.fetchone()[0]

        # Latest event
        cursor.execute("""
            SELECT event_name, event_date FROM sister_shared_events
            ORDER BY created_at DESC LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            stats['latest_event'] = f"{result[0]} ({result[1]})"
        else:
            stats['latest_event'] = 'None'

        return stats

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            self.db = None


# CLI interface for testing
if __name__ == "__main__":
    import sys

    detector = HallucinationDetector()

    # Show statistics
    print("=== Sisters Memory Statistics ===")
    stats = detector.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    print()

    # Test statements
    test_statements = [
        "この前の配信で視聴者さんがリクエストしてくれて",
        "昨日大阪で食べ歩きして美味しかった",
        "最近どう？元気にしてる？",
        "もし大阪に行くなら何を食べたい？",
    ]

    print("=== Hallucination Detection Test ===")
    for i, statement in enumerate(test_statements, 1):
        print(f"\nTest {i}: \"{statement}\"")
        result = detector.verify_statement(statement)
        print(f"  Is Hallucination: {result['is_hallucination']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Summary: {result['summary']}")
        if result['verification_results']:
            for vr in result['verification_results']:
                print(f"    - {vr['fact_type']}: {'✓' if vr['verified'] else '✗'} ({vr['evidence']})")

    detector.close()
