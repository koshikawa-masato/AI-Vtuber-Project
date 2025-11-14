"""
学習ログシステム

VPS上で会話ログを保存し、ローカル開発者が取得できるようにする
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LearningLogSystem:
    """学習ログシステム"""

    def __init__(self, db_path: str = "./learning_logs.db"):
        """
        初期化

        Args:
            db_path: 学習ログDBのパス
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"✅ 学習ログシステム初期化: {db_path}")

    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 学習ログテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                character TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                phase5_user_tier TEXT,
                phase5_response_tier TEXT,
                memories_used TEXT,
                response_time REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # インデックス作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON learning_logs(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_character
            ON learning_logs(character)
        """)

        conn.commit()
        conn.close()

    def save_log(
        self,
        character: str,
        user_id: str,
        user_message: str,
        bot_response: str,
        phase5_user_tier: str = "Safe",
        phase5_response_tier: str = "Safe",
        memories_used: Optional[List[int]] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
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
            保存したログのID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO learning_logs
            (timestamp, character, user_id, user_message, bot_response,
             phase5_user_tier, phase5_response_tier, memories_used,
             response_time, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            character,
            user_id,
            user_message,
            bot_response,
            phase5_user_tier,
            phase5_response_tier,
            json.dumps(memories_used) if memories_used else None,
            response_time,
            json.dumps(metadata) if metadata else None
        ))

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ 学習ログ保存: ID={log_id}, character={character}")
        return log_id

    def get_logs(
        self,
        since: Optional[str] = None,
        character: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        学習ログを取得

        Args:
            since: この日時以降のログを取得（ISO format）
            character: 特定のキャラクターのみ取得
            limit: 最大取得件数

        Returns:
            学習ログのリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM learning_logs WHERE 1=1"
        params = []

        if since:
            query += " AND timestamp > ?"
            params.append(since)

        if character:
            query += " AND character = ?"
            params.append(character)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        logs = []
        for row in rows:
            log = dict(zip(columns, row))
            # JSON文字列をパース
            if log.get("memories_used"):
                log["memories_used"] = json.loads(log["memories_used"])
            if log.get("metadata"):
                log["metadata"] = json.loads(log["metadata"])
            logs.append(log)

        conn.close()

        logger.info(f"✅ 学習ログ取得: {len(logs)}件")
        return logs

    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得

        Returns:
            統計情報
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 総ログ数
        cursor.execute("SELECT COUNT(*) FROM learning_logs")
        total_logs = cursor.fetchone()[0]

        # キャラクター別ログ数
        cursor.execute("""
            SELECT character, COUNT(*) as count
            FROM learning_logs
            GROUP BY character
        """)
        character_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Phase 5判定統計
        cursor.execute("""
            SELECT phase5_response_tier, COUNT(*) as count
            FROM learning_logs
            GROUP BY phase5_response_tier
        """)
        phase5_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # 平均応答時間
        cursor.execute("""
            SELECT AVG(response_time) FROM learning_logs
            WHERE response_time IS NOT NULL
        """)
        avg_response_time = cursor.fetchone()[0]

        conn.close()

        return {
            "total_logs": total_logs,
            "character_counts": character_counts,
            "phase5_stats": phase5_stats,
            "avg_response_time": avg_response_time
        }


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 学習ログシステムテスト
    log_system = LearningLogSystem(db_path="./test_learning_logs.db")

    # ログ保存テスト
    log_id = log_system.save_log(
        character="牡丹",
        user_id="user_123_hashed",
        user_message="おはよう！",
        bot_response="おはよー！今日も元気に行こうね！",
        phase5_user_tier="Safe",
        phase5_response_tier="Safe",
        memories_used=[1, 5, 10],
        response_time=2.3,
        metadata={"platform": "LINE", "test": True}
    )

    print(f"保存したログID: {log_id}")

    # ログ取得テスト
    logs = log_system.get_logs(limit=10)
    print(f"\n取得したログ: {len(logs)}件")
    for log in logs:
        print(f"  - {log['timestamp']}: {log['character']} - {log['user_message'][:20]}...")

    # 統計情報テスト
    stats = log_system.get_stats()
    print(f"\n統計情報: {json.dumps(stats, indent=2, ensure_ascii=False)}")
