"""
MySQL Database Manager (VPS版)

SSHトンネル経由でエックスサーバーのMySQLに接続
"""

import pymysql
from sshtunnel import SSHTunnelForwarder
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class MySQLManager:
    """MySQLデータベース管理クラス（SSHトンネル経由）"""

    def __init__(self):
        """初期化"""
        # SSH接続情報（環境変数から取得）
        self.ssh_config = {
            'ssh_host': os.getenv('MYSQL_SSH_HOST'),
            'ssh_port': int(os.getenv('MYSQL_SSH_PORT', '10022')),
            'ssh_username': os.getenv('MYSQL_SSH_USER'),
            'ssh_pkey': os.path.expanduser(os.getenv('MYSQL_SSH_KEY', '~/.ssh/id_rsa')),
        }

        # MySQL接続情報（環境変数から取得）
        self.mysql_config = {
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE'),
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

        self.tunnel = None
        self.connection = None
        logger.info("MySQLManager initialized")

    def connect(self) -> bool:
        """SSHトンネル経由でMySQL接続

        Returns:
            成功したらTrue
        """
        try:
            # SSHトンネル作成
            self.tunnel = SSHTunnelForwarder(
                (self.ssh_config['ssh_host'], self.ssh_config['ssh_port']),
                ssh_username=self.ssh_config['ssh_username'],
                ssh_pkey=self.ssh_config['ssh_pkey'],
                remote_bind_address=('localhost', 3306),
                local_bind_address=('127.0.0.1', 13306)
            )
            self.tunnel.start()
            logger.info(f"✅ SSHトンネル作成成功（ポート: {self.tunnel.local_bind_port}）")

            # MySQL接続
            self.connection = pymysql.connect(
                host='127.0.0.1',
                port=self.tunnel.local_bind_port,
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database'],
                charset=self.mysql_config['charset'],
                cursorclass=self.mysql_config['cursorclass'],
                connect_timeout=10
            )
            logger.info("✅ MySQL接続成功")
            return True

        except Exception as e:
            logger.error(f"MySQL接続失敗: {e}")
            if self.tunnel:
                self.tunnel.stop()
            return False

    def disconnect(self):
        """接続を切断"""
        if self.connection:
            self.connection.close()
            logger.info("MySQL接続を切断")
        if self.tunnel:
            self.tunnel.stop()
            logger.info("SSHトンネルを切断")

    def save_learning_log(
        self,
        timestamp: str,
        character: str,
        user_id: str,
        user_message: str,
        bot_response: str,
        phase5_user_tier: Optional[str] = None,
        phase5_response_tier: Optional[str] = None,
        memories_used: Optional[str] = None,
        response_time: Optional[float] = None,
        metadata: Optional[str] = None
    ) -> Optional[int]:
        """学習ログを保存

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO learning_logs (
                        `timestamp`, `character`, user_id, user_message, bot_response,
                        phase5_user_tier, phase5_response_tier, memories_used,
                        response_time, `metadata`
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                cursor.execute(sql, (
                    timestamp, character, user_id, user_message, bot_response,
                    phase5_user_tier, phase5_response_tier, memories_used,
                    response_time, metadata
                ))
                self.connection.commit()
                log_id = cursor.lastrowid
                logger.info(f"✅ 学習ログ保存: ID={log_id}, character={character}")
                return log_id

        except Exception as e:
            logger.error(f"学習ログ保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーセッションを取得

        Returns:
            セッション情報（存在しない場合はNone）
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()

        except Exception as e:
            logger.error(f"セッション取得失敗: {e}")
            return None

    def save_session(
        self,
        user_id: str,
        selected_character: Optional[str] = None,
        last_message_at: Optional[datetime] = None
    ) -> bool:
        """ユーザーセッションを保存（INSERT or UPDATE）

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, selected_character, last_message_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        selected_character = VALUES(selected_character),
                        last_message_at = VALUES(last_message_at)
                """
                cursor.execute(sql, (user_id, selected_character, last_message_at))
                self.connection.commit()
                logger.info(f"✅ セッション保存: user_id={user_id[:8]}..., character={selected_character}")
                return True

        except Exception as e:
            logger.error(f"セッション保存失敗: {e}")
            self.connection.rollback()
            return False

    def save_conversation_history(
        self,
        user_id: str,
        character: str,
        role: str,  # 'user' or 'assistant'
        message: str
    ) -> Optional[int]:
        """会話履歴を保存

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO conversation_history (user_id, `character`, `role`, message)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, character, role, message))
                self.connection.commit()
                history_id = cursor.lastrowid
                logger.debug(f"会話履歴保存: ID={history_id}, role={role}")
                return history_id

        except Exception as e:
            logger.error(f"会話履歴保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_conversation_history(
        self,
        user_id: str,
        character: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """会話履歴を取得（最新から指定件数）

        Returns:
            会話履歴のリスト（古い順）
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return []

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT `role`, message, created_at
                    FROM conversation_history
                    WHERE user_id = %s AND `character` = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(sql, (user_id, character, limit))
                results = cursor.fetchall()
                # 古い順に並び替え
                return list(reversed(results))

        except Exception as e:
            logger.error(f"会話履歴取得失敗: {e}")
            return []

    def __enter__(self):
        """コンテキストマネージャー（with文）のサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()

    def get_recent_trends(
        self,
        character: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """最新のトレンド情報を取得（daily_trendsテーブル）

        Args:
            character: 'botan', 'kasho', 'yuri', 'parent'
            limit: 取得件数（デフォルト: 3）

        Returns:
            トレンド情報のリスト（新しい順）
            各要素は {topic, content (JSON), created_at} を含む
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return []

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT topic, content, created_at
                    FROM daily_trends
                    WHERE `character` = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(sql, (character, limit))
                results = cursor.fetchall()

                # JSON文字列をパース
                for result in results:
                    if isinstance(result.get('content'), str):
                        try:
                            import json
                            result['content'] = json.loads(result['content'])
                        except json.JSONDecodeError:
                            logger.warning(f"JSON parse failed for content: {result.get('content', '')[:50]}...")

                logger.debug(f"トレンド情報取得: character={character}, count={len(results)}")
                return results

        except Exception as e:
            logger.error(f"トレンド情報取得失敗: {e}")
            return []

    def save_feedback(
        self,
        user_id: str,
        feedback_text: str
    ) -> Optional[int]:
        """フィードバックを保存

        Args:
            user_id: LINEユーザーID
            feedback_text: フィードバック内容

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO feedback (user_id, feedback_text)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (user_id, feedback_text))
                self.connection.commit()
                feedback_id = cursor.lastrowid
                logger.info(f"✅ フィードバック保存: ID={feedback_id}")
                return feedback_id

        except Exception as e:
            logger.error(f"フィードバック保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_user_mode(self, user_id: str) -> str:
        """ユーザーの選択モードを取得

        Args:
            user_id: LINEユーザーID

        Returns:
            選択モード ('auto', 'botan', 'kasho', 'yuri')
            レコードがない場合は 'auto'
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return 'auto'

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT selected_mode FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result.get('selected_mode'):
                    return result['selected_mode']
                else:
                    return 'auto'

        except Exception as e:
            logger.error(f"モード取得失敗: {e}")
            return 'auto'

    def set_user_mode(self, user_id: str, mode: str) -> bool:
        """ユーザーの選択モードを設定

        Args:
            user_id: LINEユーザーID
            mode: 選択モード ('auto', 'botan', 'kasho', 'yuri')

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, selected_mode)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE selected_mode = VALUES(selected_mode)
                """
                cursor.execute(sql, (user_id, mode))
                self.connection.commit()
                logger.info(f"✅ モード設定: user_id={user_id[:8]}..., mode={mode}")
                return True

        except Exception as e:
            logger.error(f"モード設定失敗: {e}")
            self.connection.rollback()
            return False

    def get_feedback_state(self, user_id: str) -> str:
        """フィードバック状態を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            フィードバック状態 ('none', 'waiting')
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return 'none'

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT feedback_state FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result.get('feedback_state'):
                    return result['feedback_state']
                else:
                    return 'none'

        except Exception as e:
            logger.error(f"フィードバック状態取得失敗: {e}")
            return 'none'

    def set_feedback_state(self, user_id: str, state: str) -> bool:
        """フィードバック状態を設定

        Args:
            user_id: LINEユーザーID
            state: フィードバック状態 ('none', 'waiting')

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("MySQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, feedback_state)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE feedback_state = VALUES(feedback_state)
                """
                cursor.execute(sql, (user_id, state))
                self.connection.commit()
                logger.debug(f"フィードバック状態設定: {state}")
                return True

        except Exception as e:
            logger.error(f"フィードバック状態設定失敗: {e}")
            self.connection.rollback()
            return False
