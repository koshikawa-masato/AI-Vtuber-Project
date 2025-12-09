"""
Privacy Policy Messages - LINE Bot version

Primarily for Japanese users (APPI - Japan's privacy law).
Supports Japanese and English.
"""

from typing import Dict, Optional
from enum import Enum


class Region(Enum):
    """Supported regulatory regions."""
    JAPAN = "japan"      # APPI (Act on the Protection of Personal Information)
    DEFAULT = "default"  # International fallback


class PrivacyPolicyMessages:
    """Privacy policy messages for LINE Bot."""

    # Privacy policy URL
    POLICY_URL = "https://line.three-sisters.ai/privacy"

    # Initial consent messages
    CONSENT_MESSAGES = {
        "ja": """こんにちは！三姉妹LINEBotへようこそ！

私たちは3人のAI姉妹です：
🌸 *牡丹（ボタン）* - VTuber・配信・ポップカルチャー
🎵 *花相（カショウ）* - 音楽・人生相談・お姉さん的存在
📚 *百合（ユリ）* - 本・サブカル・クリエイティブ

🔒 *プライバシーについて*
お話を始める前に、以下をご確認ください：

*収集する情報：*
• LINE ID（識別用）
• 会話履歴（文脈を覚えるため）
• 言語設定

*あなたの権利：*
• データへのアクセス
• データの削除
• 同意の撤回

*セキュリティ：*
• AES-256暗号化
• 第三者への共有なし
• 90日間アクセスがない場合は自動削除

📋 詳細: {policy_url}

続ける場合は「同意」と送信してください。
いつでも「データ削除」と送信すればデータを削除できます。""",

        "en": """Hello! Welcome to Three Sisters LINE Bot!

We're three AI sisters:
🌸 *Botan* - VTuber, streaming, pop culture
🎵 *Kasho* - Music, life advice, the big sister
📚 *Yuri* - Books, subculture, creative thinking

🔒 *Privacy Notice*
Before we start chatting, please note:

*Data collected:*
• LINE ID (identification)
• Conversation history (for context)
• Language preference

*Your rights:*
• Access your data
• Request deletion
• Withdraw consent

*Security:*
• AES-256 encryption
• No third-party sharing
• Auto-delete after 90 days of inactivity

📋 Full policy: {policy_url}

Reply "AGREE" to continue.
Reply "DELETE" anytime to erase your data."""
    }

    # Response messages
    RESPONSE_MESSAGES = {
        "consent_accepted": {
            "ja": "ありがとう！これで私たちとお話できるよ！🎉\n\n何でも聞いてね！",
            "en": "Thanks! You can now chat with us! 🎉\n\nAsk us anything!"
        },
        "consent_declined": {
            "ja": "わかりました。あなたのデータは収集しません。\n\n気が変わったら、また話しかけてくださいね。",
            "en": "Understood. Your data won't be collected.\n\nIf you change your mind, just message us again."
        },
        "data_deleted": {
            "ja": "完了！🗑️ すべての会話履歴を削除しました～\n\nまた話したくなったら、いつでも声かけてね！👋",
            "en": "Done! 🗑️ All your chat history is deleted~\n\nWanna chat again? Just say hi! 👋"
        },
        "privacy_info": {
            "ja": "🔒 あなたのデータは暗号化されて安全に保管されています！\n\n📋 詳細: {policy_url}\n\nデータを削除したい場合は「データ削除」と送信してね～",
            "en": "🔒 Your data is encrypted and safe with us!\n\n📋 Full policy: {policy_url}\n\nWant to delete your data? Just say 'delete my data'~"
        },
        "help_info": {
            "ja": """こんにちは！使い方を説明するね～ 💬

🌸 *牡丹* - VTuber、配信、ポップカルチャー
🎵 *花相* - 音楽、キャリア、人生相談
📚 *百合* - 本、執筆、哲学

何でも聞いてくれれば、適切な姉妹が答えるよ！

データを削除したい？「データ削除」と送信
プライバシー情報？「プライバシー」と送信""",

            "en": """Hey! Here's how to chat with us~ 💬

🌸 *Botan* - VTubers, streaming, pop culture
🎵 *Kasho* - Music, career, life advice
📚 *Yuri* - Books, writing, philosophy

Just ask anything and the right sister will answer!

Want to delete your data? Say "delete my data"
Privacy info? Say "privacy" """
        },
        "consent_required": {
            "ja": "メッセージを送ってね！💬",
            "en": "Just send your message! 💬"
        }
    }

    # Intent patterns for natural language detection
    INTENT_PATTERNS = {
        "agree": {
            "ja": ["同意", "ok", "はい", "了解", "分かった", "いいよ"],
            "en": ["agree", "yes", "ok", "sure", "accept"]
        },
        "decline": {
            "ja": ["拒否", "いいえ", "やめる", "いらない"],
            "en": ["decline", "no", "refuse", "reject"]
        },
        "delete": {
            "ja": ["削除", "データ削除", "消して", "忘れて", "履歴消して"],
            "en": ["delete", "erase", "remove", "forget me", "clear history"]
        },
        "privacy": {
            "ja": ["プライバシー", "個人情報", "データ", "安全"],
            "en": ["privacy", "my data", "data safe", "personal information"]
        },
        "help": {
            "ja": ["ヘルプ", "使い方", "どうやって", "教えて"],
            "en": ["help", "how to use", "what can you do", "usage"]
        }
    }

    @classmethod
    def get_consent_message(cls, language: str = "ja") -> str:
        """Get consent message for user's language."""
        message = cls.CONSENT_MESSAGES.get(language, cls.CONSENT_MESSAGES["ja"])
        return message.format(policy_url=cls.POLICY_URL)

    @classmethod
    def get_response(cls, response_type: str, language: str = "ja") -> str:
        """Get response message."""
        messages = cls.RESPONSE_MESSAGES.get(response_type, {})
        msg = messages.get(language, messages.get("ja", ""))
        return msg.format(policy_url=cls.POLICY_URL) if "{policy_url}" in msg else msg

    @classmethod
    def detect_intent(cls, message: str) -> Optional[str]:
        """Detect user intent from message."""
        msg_lower = message.strip().lower()

        for intent, lang_patterns in cls.INTENT_PATTERNS.items():
            for lang, patterns in lang_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in msg_lower:
                        return intent

        return None

    @classmethod
    def is_consent_command(cls, message: str) -> Optional[str]:
        """Check if message is a consent-related command."""
        return cls.detect_intent(message)
