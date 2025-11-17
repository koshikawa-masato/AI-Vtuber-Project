"""
フィードバック通知モジュール（Messaging API使用）

LINE Notify終了（2025年3月31日）に伴い、Messaging APIのPush Messageに変更
"""

import os
import requests
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedbackNotifier:
    """フィードバック通知クラス（Messaging API使用）"""

    def __init__(self, channel_access_token: str):
        """初期化

        Args:
            channel_access_token: LINE Bot Channel Access Token
        """
        self.channel_access_token = channel_access_token
        self.developer_user_id = os.getenv("DEVELOPER_LINE_USER_ID")

        if not self.developer_user_id:
            logger.warning("⚠️ DEVELOPER_LINE_USER_ID が設定されていません（フィードバック通知は無効）")

    def send_feedback_notification(self, user_id: str, feedback: str) -> bool:
        """フィードバック通知を開発者に送信（Messaging API Push Message）

        Args:
            user_id: フィードバックを送信したLINEユーザーID
            feedback: フィードバック内容

        Returns:
            送信成功: True, 失敗: False
        """
        if not self.developer_user_id:
            logger.warning("⚠️ 開発者USER IDが未設定（通知スキップ）")
            return False

        try:
            # メッセージ本文作成
            message_text = f"""📝 新しいフィードバック

ユーザーID: {user_id[:8]}...
内容:
{feedback}

---
受信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            # Messaging API Push Message
            url = "https://api.line.me/v2/bot/message/push"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.channel_access_token}"
            }

            data = {
                "to": self.developer_user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": message_text
                    }
                ]
            }

            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ フィードバック通知送信成功（Messaging API）")
                return True
            else:
                logger.error(f"❌ フィードバック通知送信失敗: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ フィードバック通知送信エラー: {e}")
            return False
