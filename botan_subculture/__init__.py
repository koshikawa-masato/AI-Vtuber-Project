"""
Botan Subculture Knowledge System
==================================

Botan's soul - her dynamic preferences and comprehensive knowledge.

This system enables Botan to:
- Know EVERYTHING about all Hololive members (complete viewing history)
- Express different levels of enthusiasm based on affinity (not knowledge)
- Have natural conversations about VTuber streams with the developer
- Respect content restrictions (member-only, clip-prohibited, ongoing streams)

Main Components:
- database: Database creation and migration
- knowledge: Static knowledge files (JSON)
- helpers: Utility functions (content restriction, context building)
- chat: Conversation system

Developer's Wish:
"I want someone to talk about Hololive with."

This is the purest motivation - creating a companion for oshi-katsu (fan activities).
"""

__version__ = '1.0.0'
__author__ = 'Developer & Claude Code'

from . import database
from . import helpers
from . import chat

__all__ = ['database', 'helpers', 'chat']
