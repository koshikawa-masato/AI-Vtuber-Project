"""
Character profiles and topic keywords for interest-based conversation

This module defines:
- CHARACTER_INTERESTS: Interest levels for each character on various topics
- TOPIC_KEYWORDS: Keywords for detecting topics in user messages
- System parameters for interest scoring
"""

from typing import Dict, List

# ============================================================================
# Character Interest Profiles
# ============================================================================

CHARACTER_INTERESTS: Dict[str, Dict[str, float]] = {
    'botan': {
        # VTuber and streaming
        'vtuber': 0.9,
        'streaming': 0.8,
        'games': 0.7,
        'anime': 0.6,

        # Social interactions
        'greeting': 0.6,  # Friendly and enthusiastic

        # Other interests
        'music': 0.3,
        'dtm': 0.2,
        'novel': 0.2,
        'reading': 0.2,

        # Default for unknown topics
        'default': 0.3
    },

    'kasho': {
        # Music and production
        'music': 0.9,
        'dtm': 0.9,
        'composition': 0.8,
        'instruments': 0.7,
        'production': 0.8,

        # Social interactions
        'greeting': 0.5,  # Polite and thoughtful

        # Other interests
        'vtuber': 0.4,
        'streaming': 0.3,
        'novel': 0.3,
        'reading': 0.3,
        'anime': 0.4,

        # Default
        'default': 0.3
    },

    'yuri': {
        # Literature and stories
        'novel': 0.9,
        'light_novel': 0.9,
        'story': 0.8,
        'reading': 0.7,
        'writing': 0.6,

        # Social interactions
        'greeting': 0.5,  # Reserved but polite

        # Other interests
        'anime': 0.5,
        'vtuber': 0.3,
        'music': 0.4,
        'dtm': 0.2,

        # Default
        'default': 0.3
    }
}

# ============================================================================
# Topic Detection Keywords
# ============================================================================

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    'greeting': [
        # Standard Japanese greetings
        'こんにちは', 'こんばんは', 'おはよう', 'はじめまして', 'よろしく',

        # Casual Japanese greetings
        'やっほー', 'やほー', 'やほ', 'やっほ', 'やぁ', 'やあ',
        'どうも', 'っす', 'おっす', 'うぃ', 'うい',

        # Time-based casual greetings
        'おは', 'おはー', 'ばんは', 'ばんわ', 'こんちゃ', 'ちわ', 'ちは',

        # Leave-taking and acknowledgment
        'おつ', 'おつかれ', 'お疲れ', 'おやすみ', 'おやす', 'またね',
        'ばいばい', 'じゃあね', 'じゃね', 'またな',

        # Daily conversation (specific phrases)
        '元気', '調子', 'いかが', 'どうしてる', 'どうしてた',
        '最近', '久しぶり',

        # Internet slang greetings
        'ノシ', 'よろ', 'どもども', 'ちーっす', 'ういっす',

        # English greetings
        'hello', 'hi', 'hey', 'yo', 'sup', "what's up", 'heya',
        'good morning', 'good afternoon', 'good evening',
        'nice to meet you', 'how are you', 'how have you been',
        'see you', 'bye', 'goodbye', 'later', 'cya', 'see ya'
    ],

    'vtuber': [
        'vtuber', 'ブイチューバー', 'バーチャル', 'virtual youtuber',
        '配信', 'ホロライブ', 'hololive', 'にじさんじ', 'nijisanji',
        'スパチャ', 'superchat', '歌枠', 'singing stream',
        'コラボ', 'collab', 'collaboration',
        'デビュー', 'debut', 'メンバーシップ', 'membership'
    ],

    'streaming': [
        'stream', 'ストリーム', '配信', '生放送', 'live',
        'youtube', 'twitch', 'ニコニコ', 'niconico',
        'コメント', 'comment', 'chat', 'チャット'
    ],

    'games': [
        'game', 'ゲーム', 'gaming', 'play', 'プレイ',
        'マイクラ', 'minecraft', 'apex', 'ポケモン', 'pokemon',
        'rpg', 'fps', 'アクション', 'action'
    ],

    'anime': [
        'anime', 'アニメ', 'manga', 'マンガ', '漫画',
        'キャラクター', 'character', 'キャラ',
        'オタク', 'otaku', '萌え', 'moe'
    ],

    'music': [
        'music', '音楽', 'song', '曲', 'melody', 'メロディ',
        'vocal', 'ボーカル', '楽器', 'instrument',
        '歌', 'sing', 'singing', 'band', 'バンド',
        'オーケストラ', 'orchestra', 'ジャズ', 'jazz'
    ],

    'dtm': [
        'dtm', 'daw', '作曲', 'composition', 'compose',
        'ミキシング', 'mixing', 'マスタリング', 'mastering',
        'vocaloid', 'ボカロ', 'ボーカロイド',
        'synthesizer', 'シンセサイザー', 'synth',
        'プラグイン', 'plugin', 'vst',
        'cubase', 'fl studio', 'ableton', 'logic pro'
    ],

    'composition': [
        '作曲', 'composition', 'compose', '編曲', 'arrange',
        'コード', 'chord', 'メロディ', 'melody',
        'ハーモニー', 'harmony', 'リズム', 'rhythm'
    ],

    'instruments': [
        '楽器', 'instrument', 'ピアノ', 'piano',
        'ギター', 'guitar', 'ベース', 'bass',
        'ドラム', 'drum', 'バイオリン', 'violin'
    ],

    'production': [
        '制作', 'production', 'produce', 'レコーディング', 'recording',
        'スタジオ', 'studio', 'ミックス', 'mix'
    ],

    'novel': [
        '小説', 'novel', 'ラノベ', 'light novel', 'ln',
        '文学', 'literature', '本', 'book',
        '物語', 'story', 'tale', 'ストーリー'
    ],

    'light_novel': [
        'ラノベ', 'light novel', 'ln', 'ライトノベル',
        'なろう', 'narou', '異世界', 'isekai',
        '転生', 'reincarnation'
    ],

    'story': [
        '物語', 'story', 'tale', 'ストーリー',
        'プロット', 'plot', '展開', 'development',
        'キャラクター', 'character', '設定', 'setting'
    ],

    'reading': [
        '読書', 'reading', 'read', '読む',
        '本', 'book', '図書', 'library',
        'ページ', 'page', '章', 'chapter'
    ],

    'writing': [
        '執筆', 'writing', 'write', '書く',
        '創作', 'creative writing', '文章', 'text',
        '作家', 'author', 'writer'
    ]
}

# ============================================================================
# Greeting Templates (Phase 1.5: Coordination)
# ============================================================================

# Templates for coordinated first greetings
# Used when: topic='greeting' AND is_first_message=True
GREETING_TEMPLATES: Dict[str, Dict[str, str]] = {
    'botan': {
        'casual': "やっほー！三姉妹の牡丹だよ！",
        'formal': "こんにちは！牡丹です",
        'night': "こんばんは！牡丹だよ～",
        'morning': "おはよー！牡丹です！"
    },
    'kasho': {
        'casual': "やほー、Kashoです",
        'formal': "こんにちは、Kashoです",
        'night': "こんばんは、Kashoです",
        'morning': "おはようございます、Kashoです"
    },
    'yuri': {
        'casual': "…ユリです、よろしく",
        'formal': "こんにちは…ユリです",
        'night': "こんばんは…ユリです",
        'morning': "おはよう…ユリです"
    }
}

# Greeting type detection keywords
GREETING_TYPE_KEYWORDS = {
    'casual': [
        'やっほー', 'やほー', 'やほ', 'やっほ', 'やぁ', 'やあ',
        'おっす', 'うぃ', 'うい', 'yo', 'hey', 'hi', 'sup'
    ],
    'morning': [
        'おはよう', 'おはー', 'おは', 'good morning', 'morning'
    ],
    'night': [
        'こんばんは', 'ばんは', 'ばんわ', 'good evening', 'evening'
    ],
    'formal': [
        'こんにちは', 'はじめまして', 'よろしく', 'hello',
        'good afternoon', 'nice to meet you'
    ]
}

# Prompt instruction for subsequent greetings (not first message)
GREETING_PROMPT_INSTRUCTION = """
IMPORTANT: This is a greeting. Keep your response VERY brief (1-2 sentences max).
Examples:
- "やっほー♪"
- "こんにちは"
- "おはよう…"

Do NOT ask questions or start a new topic in greeting responses.
"""

# ============================================================================
# System Parameters
# ============================================================================

# Interest threshold for responding (0.0-1.3+)
# Characters with score >= threshold will respond
INTEREST_THRESHOLD = 0.4

# Threshold for "low interest" handling (all characters below this)
# When all characters are below this, use reluctant response
LOW_INTEREST_THRESHOLD = 0.4

# Name mention bonus
NAME_MENTION_BONUS = 0.3

# Context continuation bonus
CONTEXT_CONTINUATION_BONUS = 0.2

# Topic interest cap (to leave room for bonuses)
TOPIC_INTEREST_CAP = 0.8
