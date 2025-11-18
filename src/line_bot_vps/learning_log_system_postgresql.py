"""
学習ログシステム（PostgreSQL版）

XServer VPS PostgreSQLに会話ログを保存
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .postgresql_manager import PostgreSQLManager

logger = logging.getLogger(__name__)


class LearningLogSystemPostgreSQL:
    """学習ログシステム（PostgreSQL版）"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        self.connected = False
        logger.info("✅ 学習ログシステム初期化（PostgreSQL）")

    def connect(self) -> bool:
        """PostgreSQL接続"""
        if not self.connected:
            self.connected = self.pg_manager.connect()
        return self.connected

    def disconnect(self):
        """PostgreSQL切断"""
        if self.connected:
            self.pg_manager.disconnect()
            self.connected = False

    def save_log(
        self,
        character: str,
        user_id: str,
        user_message: str,
        bot_response: str,
        phase5_user_tier: Optional[int] = None,
        phase5_response_tier: Optional[int] = None,
        memories_used: Optional[List[int]] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        学習ログを保存

        Args:
            character: キャラクター名
            user_id: ユーザーID（ハッシュ化済み）
            user_message: ユーザーメッセージ
            bot_response: Bot応答
            phase5_user_tier: ユーザーメッセージのPhase 5判定
            phase5_response_tier: Bot応答のPhase 5判定
            memories_used: 使用した記憶ID
            response_time: 応答時間（秒）
            metadata: その他のメタデータ

        Returns:
            保存したログのID（失敗時はNone）
        """
        if not self.connected:
            if not self.connect():
                logger.error("PostgreSQL未接続のため、ログ保存失敗")
                return None

        timestamp = datetime.now().isoformat()

        log_id = self.pg_manager.save_learning_log(
            timestamp=timestamp,
            character=character,
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            phase5_user_tier=phase5_user_tier,
            phase5_response_tier=phase5_response_tier,
            memories_used=json.dumps(memories_used) if memories_used else None,
            response_time=response_time,
            metadata=json.dumps(metadata) if metadata else None
        )

        if log_id:
            logger.info(f"✅ 学習ログ保存: ID={log_id}, character={character}")
        return log_id

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 学習ログシステムテスト
    with LearningLogSystemPostgreSQL() as log_system:
        # ログ保存テスト
        log_id = log_system.save_log(
            character="botan",
            user_id="user_123_hashed",
            user_message="おはよう！",
            bot_response="おはよー！今日も元気に行こうね！",
            phase5_user_tier=1,  # Phase 5: Safe=1, Moderate=2, Risky=3
            phase5_response_tier=1,
            memories_used=[1, 5, 10],
            response_time=2.3,
            metadata={"platform": "LINE", "test": True}
        )

        print(f"保存したログID: {log_id}")
