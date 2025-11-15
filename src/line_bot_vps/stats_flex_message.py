"""
統計表示用 Flex Message

ユーザーの会話統計をカード形式で表示
"""

from typing import Dict, Any, Optional


def create_stats_flex_message(
    total_messages: int = 0,
    botan_count: int = 0,
    kasho_count: int = 0,
    yuri_count: int = 0,
    current_character: Optional[str] = None
) -> Dict[str, Any]:
    """統計のFlex Messageを作成

    Args:
        total_messages: 総会話回数
        botan_count: 牡丹との会話回数
        kasho_count: Kashoとの会話回数
        yuri_count: ユリとの会話回数
        current_character: 現在選択中のキャラクター

    Returns:
        Flex Message（Bubble形式）
    """
    # お気に入りキャラクターを判定
    favorite_char = _get_favorite_character(botan_count, kasho_count, yuri_count)

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 あなたの統計",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#50C878"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                _create_total_count_box(total_messages),
                _create_separator(),
                _create_section_title("👭 キャラクター別の会話回数"),
                _create_character_stat("牡丹（Botan）", botan_count, total_messages, "#FF69B4"),
                _create_character_stat("Kasho（花相）", kasho_count, total_messages, "#9370DB"),
                _create_character_stat("ユリ（Yuri）", yuri_count, total_messages, "#87CEEB"),
                _create_separator(),
                _create_favorite_box(favorite_char),
                _create_separator(),
                _create_section_title("🎯 現在の状態"),
                _create_bullet_item(f"選択中: {_get_character_name(current_character)}"),
                _create_separator(),
                {
                    "type": "text",
                    "text": "💡 会話を重ねるほど、三姉妹の記憶が鮮明になります",
                    "size": "xs",
                    "wrap": True,
                    "color": "#999999",
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "統計を更新",
                        "data": "action=stats"
                    },
                    "style": "link",
                    "color": "#50C878"
                }
            ]
        }
    }


def _get_favorite_character(botan: int, kasho: int, yuri: int) -> str:
    """お気に入りキャラクターを判定"""
    if botan == kasho == yuri == 0:
        return "まだありません"

    max_count = max(botan, kasho, yuri)
    if botan == max_count:
        return "牡丹（Botan）"
    elif kasho == max_count:
        return "Kasho（花相）"
    else:
        return "ユリ（Yuri）"


def _get_character_name(character: Optional[str]) -> str:
    """キャラクター名を取得"""
    names = {
        "botan": "牡丹（Botan）",
        "kasho": "Kasho（花相）",
        "yuri": "ユリ（Yuri）"
    }
    return names.get(character, "未選択")


def _create_total_count_box(count: int) -> Dict[str, Any]:
    """総会話回数ボックスを作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "総会話回数",
                "size": "sm",
                "color": "#AAAAAA"
            },
            {
                "type": "text",
                "text": f"{count} 回",
                "size": "xxl",
                "weight": "bold",
                "color": "#50C878"
            }
        ],
        "paddingAll": "md",
        "backgroundColor": "#F0F8F0",
        "cornerRadius": "md"
    }


def _create_character_stat(name: str, count: int, total: int, color: str) -> Dict[str, Any]:
    """キャラクター別統計を作成"""
    percentage = (count / total * 100) if total > 0 else 0

    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": name,
                "size": "sm",
                "flex": 3,
                "color": "#555555"
            },
            {
                "type": "text",
                "text": f"{count}回",
                "size": "sm",
                "flex": 1,
                "align": "end",
                "weight": "bold",
                "color": color
            },
            {
                "type": "text",
                "text": f"({percentage:.0f}%)",
                "size": "xs",
                "flex": 1,
                "align": "end",
                "color": "#AAAAAA"
            }
        ],
        "margin": "md"
    }


def _create_favorite_box(favorite: str) -> Dict[str, Any]:
    """お気に入りボックスを作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "🌟 一番よく話すキャラクター",
                "size": "sm",
                "color": "#AAAAAA"
            },
            {
                "type": "text",
                "text": favorite,
                "size": "lg",
                "weight": "bold",
                "color": "#50C878",
                "margin": "xs"
            }
        ]
    }


def _create_section_title(title: str) -> Dict[str, Any]:
    """セクションタイトルを作成"""
    return {
        "type": "text",
        "text": title,
        "weight": "bold",
        "size": "md",
        "margin": "md",
        "color": "#333333"
    }


def _create_bullet_item(text: str) -> Dict[str, Any]:
    """箇条書きアイテムを作成"""
    return {
        "type": "text",
        "text": f"• {text}",
        "size": "sm",
        "wrap": True,
        "margin": "sm",
        "color": "#555555"
    }


def _create_separator() -> Dict[str, Any]:
    """区切り線を作成"""
    return {
        "type": "separator",
        "margin": "lg"
    }
