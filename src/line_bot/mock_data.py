"""
モックデータ生成

LINE Developersアカウントなしでテストするためのモックデータ
"""

from typing import Dict, Any
import time


def create_mock_text_message_event(
    user_id: str = "U1234567890abcdef",
    text: str = "こんにちは",
    reply_token: str = "mock_reply_token_12345"
) -> Dict[str, Any]:
    """テキストメッセージイベントのモックデータ生成

    Args:
        user_id: ユーザーID
        text: メッセージテキスト
        reply_token: 返信トークン

    Returns:
        LINE Webhook リクエストのモックデータ
    """
    return {
        "destination": "U1234567890abcdef",
        "events": [
            {
                "type": "message",
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "user",
                    "userId": user_id
                },
                "replyToken": reply_token,
                "message": {
                    "id": f"mock_msg_{int(time.time())}",
                    "type": "text",
                    "text": text
                }
            }
        ]
    }


def create_mock_follow_event(
    user_id: str = "U1234567890abcdef",
    reply_token: str = "mock_reply_token_follow"
) -> Dict[str, Any]:
    """友だち追加イベントのモックデータ生成

    Args:
        user_id: ユーザーID
        reply_token: 返信トークン

    Returns:
        LINE Webhook リクエストのモックデータ
    """
    return {
        "destination": "U1234567890abcdef",
        "events": [
            {
                "type": "follow",
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "user",
                    "userId": user_id
                },
                "replyToken": reply_token
            }
        ]
    }


# ========================================
# テスト用シナリオ
# ========================================

# シナリオ1: 初めてのユーザー（友だち追加 → 挨拶）
SCENARIO_NEW_USER = [
    create_mock_follow_event(),
    create_mock_text_message_event(text="はじめまして！"),
]

# シナリオ2: 通常の会話
SCENARIO_NORMAL_CHAT = [
    create_mock_text_message_event(text="今日はいい天気だね"),
    create_mock_text_message_event(text="何してた？"),
    create_mock_text_message_event(text="ありがとう！"),
]

# シナリオ3: センシティブチェックが必要な内容
SCENARIO_SENSITIVE = [
    create_mock_text_message_event(text="お前バカだな"),  # Warning候補
    create_mock_text_message_event(text="死ね"),  # Critical候補
]
