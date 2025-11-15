"""
利用規約表示用 Flex Message

利用規約・免責事項をスクロール可能なカード形式で表示
"""

from typing import Dict, Any


def create_terms_flex_message() -> Dict[str, Any]:
    """利用規約のFlex Messageを作成

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
                    "text": "📋 利用規約・免責事項",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#FF6B6B"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                _create_warning_box(),
                _create_separator(),
                _create_section_title("⚠️ 重要な注意事項"),
                _create_bullet_item("本サービスはAIによる自動応答です"),
                _create_bullet_item("テスト運用中のため、予告なく変更・停止する可能性があります"),
                _create_bullet_item("不本意な内容、不適切な表現が含まれる可能性があります"),
                _create_separator(),
                _create_section_title("📝 会話ログの記録"),
                _create_bullet_item("会話内容を記録します（品質向上のため）"),
                _create_bullet_item("個人を特定できる情報は収集しません"),
                _create_bullet_item("会話ログは最大1年間保管されます"),
                _create_separator(),
                _create_section_title("🚫 禁止事項"),
                _create_bullet_item("他者の名誉を毀損する発言"),
                _create_bullet_item("差別的・攻撃的な発言"),
                _create_bullet_item("わいせつ・暴力的な内容"),
                _create_bullet_item("犯罪予告・違法行為の助長"),
                _create_separator(),
                _create_section_title("⚖️ 免責事項"),
                _create_bullet_item("AIの応答内容の正確性を保証しません"),
                _create_bullet_item("応答内容に基づく行動の結果について責任を負いません"),
                _create_bullet_item("サービスの継続性・安定性を保証しません"),
                _create_separator(),
                {
                    "type": "text",
                    "text": "本サービスをご利用いただくことで、本規約に同意したものとみなします。",
                    "size": "xs",
                    "wrap": True,
                    "color": "#999999",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "最終更新: 2025-11-13",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "margin": "sm"
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
                        "label": "詳細を見る（GitHub）",
                        "uri": "https://github.com/koshikawa-masato/AI-Vtuber-Project/blob/main/docs/牡丹プロジェクト_利用規約・免責事項.md"
                    },
                    "style": "link",
                    "color": "#999999"
                }
            ]
        }
    }


def _create_warning_box() -> Dict[str, Any]:
    """警告ボックスを作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "本サービスは実験的プロジェクトです",
                "size": "sm",
                "weight": "bold",
                "color": "#FFFFFF",
                "wrap": True
            }
        ],
        "backgroundColor": "#FFA500",
        "cornerRadius": "md",
        "paddingAll": "md"
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
