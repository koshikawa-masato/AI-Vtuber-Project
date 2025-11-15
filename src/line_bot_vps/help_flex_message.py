"""
ヘルプ表示用 Flex Message

使い方・FAQ・トラブルシューティングをカード形式で表示
"""

from typing import Dict, Any


def create_help_flex_message() -> Dict[str, Any]:
    """ヘルプのFlex Messageを作成

    Returns:
        Flex Message（Bubble形式）
    """
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "ℹ️ ヘルプ・使い方",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#4A90E2"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                _create_section_title("🎯 基本的な使い方"),
                _create_bullet_item("リッチメニューから三姉妹を選択"),
                _create_bullet_item("選択したキャラクターと会話ができます"),
                _create_bullet_item("いつでもキャラクターを切り替え可能"),
                _create_separator(),
                _create_section_title("👭 三姉妹について"),
                _create_character_info("牡丹（ぼたん）", "17歳・次女", "社交的で明るいギャル系"),
                _create_character_info("Kasho（かしょう）", "19歳・長女", "責任感が強く論理的"),
                _create_character_info("ユリ（ゆり）", "15歳・三女", "好奇心旺盛で洞察力が深い"),
                _create_separator(),
                _create_section_title("💡 ヒント"),
                _create_bullet_item("各キャラクターは過去の記憶を持っています"),
                _create_bullet_item("同じ質問でもキャラクターによって答えが異なります"),
                _create_bullet_item("会話を重ねるほど記憶が鮮明になります"),
                _create_separator(),
                _create_section_title("❓ よくある質問"),
                _create_faq_item("Q: 応答が遅いのですが？", "A: AI処理に数秒かかる場合があります。混雑時はさらに時間がかかることがあります。"),
                _create_faq_item("Q: データは記録されますか？", "A: 会話ログは品質向上のため記録されますが、個人を特定できる情報は収集しません。"),
                _create_separator(),
                {
                    "type": "text",
                    "text": "🔍 詳しい情報はGitHubをご覧ください",
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
                        "type": "uri",
                        "label": "GitHubで詳細を見る",
                        "uri": "https://github.com/koshikawa-masato/AI-Vtuber-Project"
                    },
                    "style": "link",
                    "color": "#4A90E2"
                }
            ]
        }
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


def _create_character_info(name: str, age_role: str, personality: str) -> Dict[str, Any]:
    """キャラクター情報を作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": f"{name}（{age_role}）",
                "size": "sm",
                "weight": "bold",
                "color": "#333333"
            },
            {
                "type": "text",
                "text": personality,
                "size": "xs",
                "color": "#777777",
                "wrap": True
            }
        ],
        "margin": "sm"
    }


def _create_faq_item(question: str, answer: str) -> Dict[str, Any]:
    """FAQ項目を作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": question,
                "size": "sm",
                "weight": "bold",
                "color": "#4A90E2",
                "wrap": True
            },
            {
                "type": "text",
                "text": answer,
                "size": "xs",
                "color": "#555555",
                "wrap": True,
                "margin": "xs"
            }
        ],
        "margin": "md"
    }


def _create_separator() -> Dict[str, Any]:
    """区切り線を作成"""
    return {
        "type": "separator",
        "margin": "lg"
    }
