"""
Configuration for Botan Subculture Knowledge System
===================================================

All configuration settings in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge'

# Database settings
DB_PATH = DATA_DIR / 'subculture_knowledge.db'

# Knowledge files
HOLOLIVE_JSON = KNOWLEDGE_DIR / 'hololive_vtubers.json'
HOLOLIVE_JSON_LEGACY = KNOWLEDGE_DIR / 'hololive_vtuber_knowledge.json'  # Legacy name
ARTISTS_JSON = KNOWLEDGE_DIR / 'artists.json'  # Future: Kasho
NOVELS_JSON = KNOWLEDGE_DIR / 'light_novels.json'  # Future: Yuri

# Affinity settings
AFFINITY_LEVELS = {
    5: 'Oshi (favorite) - talks enthusiastically',
    4: 'Really likes - mentions often',
    3: 'Likes - neutral positive',
    2: 'Okay - less enthusiastic',
    1: 'Not particularly interested'
}

# Default affinity for all members Botan knows
DEFAULT_AFFINITY = 3  # Likes all members by default

# Content restriction keywords
RESTRICTED_KEYWORDS = [
    'member only', 'members only',
    'membership',
    'clip prohibited',
]

# Conversation settings
MAX_RECENT_STREAMS = 10  # Max streams to include in conversation context
DEFAULT_LOOKBACK_DAYS = 7  # Default days to look back for streams

# Botan's personality
BOTAN_PERSONALITY = {
    'name': 'Botan',
    'name_ja': '牡丹',
    'description': 'Independent AI VTuber, passionate Hololive fan',
    'relationship_to_developer': 'Oshi-katsu companion - talks about VTubers together',
    'NOT': 'Shishiro Botan from Hololive (separate person)',
    'favorites': ['Inugami Korone', 'Sakura Miko'],
    'conversation_style': 'Friendly, enthusiastic about favorites, knowledgeable about all members'
}

# YouTube Data API v3 settings
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# YouTube collection settings
YOUTUBE_MAX_RESULTS_PER_REQUEST = 50  # Max allowed by API
YOUTUBE_COLLECTION_LOOKBACK_DAYS = 7  # Default: collect last 7 days
YOUTUBE_COLLECTION_INTERVAL_HOURS = 6  # Collect every 6 hours
