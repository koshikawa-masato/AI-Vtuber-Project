"""
LINE Notify 連携モジュール

フィードバック通知を開発者に送信
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LineNotify:
    """LINE Notify 通知クラス"""

    def __init__(self):
        """初期化"""
        self.token = os.getenv("LINE_NOTIFY_TOKEN")

        if not self.token:
            logger.warning("⚠️ LINE_NOTIFY_TOKEN が設定されていません（フィードバック通知は無効）")

    def send_feedback_notification(self, user_id: str, feedback: str) -> bool:
        """フィードバック通知を開発者に送信

        Args:
            user_id: LINEユーザーID
            feedback: フィードバック内容

        Returns:
            送信成功: True, 失敗: False
        """
        if not self.token:
            logger.warning("⚠️ LINE Notify トークンが未設定（通知スキップ）")
            return False

        try:
            from datetime import datetime

            message = f"""
📝 新しいフィードバック

ユーザーID: {user_id[:8]}...
内容:
{feedback}

---
受信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            data = {
                "message": message
            }

            response = requests.post(
                "https://notify-api.line.me/api/notify",
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ LINE Notify 送信成功")
                return True
            else:
                logger.error(f"❌ LINE Notify 送信失敗: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ LINE Notify 送信エラー: {e}")
            return False
