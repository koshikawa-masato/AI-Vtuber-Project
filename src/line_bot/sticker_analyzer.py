"""
スタンプVLM解析モジュール

LINE スタンプの画像をVLMで解析し、感情や内容を判定する。
解析結果はキャッシュして再利用する。
"""

import sqlite3
import logging
import base64
import requests
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class StickerAnalyzer:
    """スタンプVLM解析クラス"""

    def __init__(self, llm, cache_db_path: str = None):
        """
        Args:
            llm: TracedLLMインスタンス
            cache_db_path: キャッシュDBパス
        """
        self.llm = llm
        self.cache_db_path = cache_db_path or "/home/koshikawa/AI-Vtuber-Project/src/line_bot/database/sticker_cache.db"

        # キャッシュDB初期化
        self._init_cache_db()

        logger.info(f"StickerAnalyzer初期化完了: cache={self.cache_db_path}")

    def _init_cache_db(self):
        """キャッシュDB初期化"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sticker_analysis (
                sticker_id TEXT PRIMARY KEY,
                package_id TEXT NOT NULL,
                emotion TEXT,
                description TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        logger.info("スタンプ解析キャッシュDB初期化完了")

    def get_sticker_image_url(self, sticker_id: str) -> str:
        """スタンプ画像URLを取得

        Args:
            sticker_id: スタンプID

        Returns:
            スタンプ画像URL
        """
        # LINE公式のスタンプ画像URL（Android版）
        return f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/android/sticker.png"

    def download_sticker_image(self, sticker_id: str) -> Optional[bytes]:
        """スタンプ画像をダウンロード

        Args:
            sticker_id: スタンプID

        Returns:
            画像バイナリ、失敗時はNone
        """
        url = self.get_sticker_image_url(sticker_id)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            logger.info(f"スタンプ画像ダウンロード成功: sticker_id={sticker_id}, size={len(response.content)} bytes")
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"スタンプ画像ダウンロード失敗: sticker_id={sticker_id}, error={e}")
            return None

    def get_cached_analysis(self, sticker_id: str, package_id: str) -> Optional[Dict[str, str]]:
        """キャッシュから解析結果を取得

        Args:
            sticker_id: スタンプID
            package_id: パッケージID

        Returns:
            {"emotion": str, "description": str} or None
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT emotion, description FROM sticker_analysis WHERE sticker_id = ? AND package_id = ?",
            (sticker_id, package_id)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            logger.info(f"スタンプ解析キャッシュヒット: sticker_id={sticker_id}")
            return {
                "emotion": row[0],
                "description": row[1]
            }

        return None

    def save_analysis_cache(self, sticker_id: str, package_id: str, emotion: str, description: str):
        """解析結果をキャッシュに保存

        Args:
            sticker_id: スタンプID
            package_id: パッケージID
            emotion: 感情（happy, sad, love, surprise等）
            description: 説明文
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO sticker_analysis (sticker_id, package_id, emotion, description)
            VALUES (?, ?, ?, ?)
            """,
            (sticker_id, package_id, emotion, description)
        )

        conn.commit()
        conn.close()

        logger.info(f"スタンプ解析キャッシュ保存: sticker_id={sticker_id}, emotion={emotion}")

    def analyze_sticker(self, sticker_id: str, package_id: str) -> Dict[str, Any]:
        """スタンプをVLMで解析

        Args:
            sticker_id: スタンプID
            package_id: パッケージID

        Returns:
            {
                "emotion": str,  # happy, sad, love, surprise, angry, neutral等
                "description": str,  # 日本語の説明
                "cached": bool  # キャッシュヒットしたか
            }
        """
        # キャッシュ確認
        cached = self.get_cached_analysis(sticker_id, package_id)
        if cached:
            return {
                "emotion": cached["emotion"],
                "description": cached["description"],
                "cached": True
            }

        # スタンプ画像ダウンロード
        image_data = self.download_sticker_image(sticker_id)
        if not image_data:
            logger.warning(f"スタンプ画像ダウンロード失敗: sticker_id={sticker_id}")
            return {
                "emotion": "unknown",
                "description": "スタンプ画像が取得できませんでした",
                "cached": False
            }

        # Base64エンコード
        base64_image = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/png;base64,{base64_image}"

        # VLMでスタンプ解析
        vlm_prompt = """このLINEスタンプの画像を見て、以下の情報を抽出してください。

【感情分類】(1つ選択)
- happy: 喜び、笑顔、楽しい
- love: 愛情、ハート、好き
- sad: 悲しい、泣く、落ち込み
- surprise: 驚き、びっくり
- angry: 怒り、不満
- greeting: 挨拶、おはよう、おやすみ
- thanks: ありがとう、感謝
- neutral: その他

【日本語説明】(10文字以内)
スタンプの内容を簡潔に説明してください（例: 「笑顔で喜んでいる」「ハートを送っている」）

【回答フォーマット】（必ずこの形式で回答）
感情: [感情分類]
説明: [日本語説明]

回答:"""

        try:
            result = self.llm.generate(
                prompt=vlm_prompt,
                image_url=image_url,
                temperature=0.3,  # 低めで安定した解析
                max_tokens=100,
                metadata={
                    "sticker_analysis": True,
                    "sticker_id": sticker_id,
                    "package_id": package_id
                }
            )

            response_text = result.get("response", "").strip()
            logger.info(f"VLM解析結果: {response_text}")

            # パース
            emotion = "neutral"
            description = "スタンプ"

            for line in response_text.split("\n"):
                line = line.strip()
                if line.startswith("感情:") or line.startswith("感情："):
                    emotion = line.split(":", 1)[-1].split("：", 1)[-1].strip().lower()
                elif line.startswith("説明:") or line.startswith("説明："):
                    description = line.split(":", 1)[-1].split("：", 1)[-1].strip()

            # キャッシュに保存
            self.save_analysis_cache(sticker_id, package_id, emotion, description)

            logger.info(f"スタンプ解析完了: emotion={emotion}, description={description}")

            return {
                "emotion": emotion,
                "description": description,
                "cached": False
            }

        except Exception as e:
            logger.error(f"VLMスタンプ解析エラー: {e}")
            return {
                "emotion": "unknown",
                "description": "解析に失敗しました",
                "cached": False
            }
