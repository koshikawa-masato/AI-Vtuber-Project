"""
Conversation module for natural sister interaction

Phase 1: Interest-based response selection (implemented)
Phase 2: Response timing and interruption (future)
Phase 3: Turn ending detection (future)
Phase 4: User interruption handling (future)
"""

from .interest_analyzer import InterestAnalyzer

__all__ = [
    'InterestAnalyzer'
]
