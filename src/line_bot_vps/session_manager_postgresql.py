"""
User Session Manager (PostgreSQL版)

ユーザーセッション管理（キャラクター選択、会話履歴など）
"""

import logging
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from .postgresql_manager import PostgreSQLManager
import psycopg2.extras

logger = logging.getLogger(__name__)

CharacterType = Literal["botan", "kasho", "yuri"]


class SessionManagerPostgreSQL:
    """セッション管理クラス（PostgreSQL版）"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        self.connected = False
        logger.info("SessionManager initialized (PostgreSQL)")

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

    def get_character(self, user_id: str) -> Optional[CharacterType]:
        """ユーザーの選択キャラクターを取得

        Args:
            user_id: LINEユーザーID

        Returns:
            選択されたキャラクター（未選択の場合はNone）
        """
        if not self.connected:
            if not self.connect():
                return None

        session = self.pg_manager.get_session(user_id)
        if session:
            return session.get('selected_character')
        return None

    def get_character_or_default(
        self,
        user_id: str,
        default: CharacterType = "botan"
    ) -> CharacterType:
        """ユーザーの選択キャラクターを取得（未選択の場合はデフォルト）

        Args:
            user_id: LINEユーザーID
            default: デフォルトキャラクター

        Returns:
            選択されたキャラクター
        """
        character = self.get_character(user_id)
        if character is None:
            logger.info(f"User {user_id[:8]}... has no character selected, using default: {default}")
            return default
        return character

    def set_character(self, user_id: str, character: CharacterType) -> bool:
        """ユーザーの選択キャラクターを設定

        Args:
            user_id: LINEユーザーID
            character: 選択されたキャラクター（botan, kasho, yuri）

        Returns:
            成功したらTrue
        """
        if not self.connected:
            if not self.connect():
                return False

        # 既存のセッションを取得
        session = self.pg_manager.get_session(user_id)
        old_character = session.get('selected_character') if session else None

        # セッション更新
        success = self.pg_manager.save_session(
            user_id=user_id,
            selected_character=character,
            last_message_at=datetime.now()
        )

        if success:
            if old_character != character:
                logger.info(f"User {user_id[:8]}... changed character: {old_character} -> {character}")
            else:
                logger.info(f"User {user_id[:8]}... selected character: {character}")

        return success

    def update_last_message_time(self, user_id: str, character: str = None) -> bool:
        """最終メッセージ時刻を更新

        Args:
            user_id: LINEユーザーID
            character: 現在のキャラクター名（指定すればselected_characterも更新）

        Returns:
            成功したらTrue
        """
        if not self.connected:
            if not self.connect():
                return False

        # キャラクターが指定されていない場合は既存のセッションから取得
        if character is None:
            session = self.pg_manager.get_session(user_id)
            character = session.get('selected_character') if session else None

        # セッション更新
        return self.pg_manager.save_session(
            user_id=user_id,
            selected_character=character,
            last_message_at=datetime.now()
        )

    def save_conversation(
        self,
        user_id: str,
        character: str,
        user_message: str,
        bot_response: str
    ) -> bool:
        """会話履歴を保存

        Args:
            user_id: LINEユーザーID
            character: キャラクター名
            user_message: ユーザーメッセージ
            bot_response: Bot応答

        Returns:
            成功したらTrue
        """
        if not self.connected:
            if not self.connect():
                logger.error(f"❌ PostgreSQL接続失敗のため会話履歴を保存できません: user={user_id[:8]}...")
                return False

        # ユーザーメッセージを保存
        user_history_id = self.pg_manager.save_conversation_history(
            user_id=user_id,
            character=character,
            role='user',
            message=user_message
        )

        # Bot応答を保存
        bot_history_id = self.pg_manager.save_conversation_history(
            user_id=user_id,
            character=character,
            role='assistant',
            message=bot_response
        )

        return user_history_id is not None and bot_history_id is not None

    def get_conversation_history(
        self,
        user_id: str,
        character: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """会話履歴を取得（LLMに渡す形式）

        Args:
            user_id: LINEユーザーID
            character: キャラクター名
            limit: 最大取得件数

        Returns:
            会話履歴のリスト [{"role": "user", "content": "..."}, ...]
        """
        if not self.connected:
            if not self.connect():
                return []

        history = self.pg_manager.get_conversation_history(
            user_id=user_id,
            character=character,
            limit=limit
        )

        # LLM用のフォーマットに変換
        formatted_history = []
        for item in history:
            formatted_history.append({
                "role": item['role'],
                "content": item['message']
            })

        return formatted_history

    def get_user_stats(self, user_id: str) -> Dict[str, int]:
        """ユーザーの会話統計を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            統計情報 {"total": 総数, "botan": 牡丹, "kasho": Kasho, "yuri": ユリ}
        """
        if not self.connected:
            if not self.connect():
                return {"total": 0, "botan": 0, "kasho": 0, "yuri": 0}

        try:
            connection = self.pg_manager.connection
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # キャラクター別会話数を取得
                cursor.execute("""
                    SELECT character, COUNT(*) as count
                    FROM conversation_history
                    WHERE user_id = %s AND role = 'user'
                    GROUP BY character
                """, (user_id,))
                results = cursor.fetchall()

                # 集計
                stats = {"total": 0, "botan": 0, "kasho": 0, "yuri": 0}
                for row in results:
                    char = row['character']
                    count = row['count']
                    stats[char] = count
                    stats['total'] += count

                return stats

        except Exception as e:
            logger.error(f"❌ 統計取得エラー: {e}")
            return {"total": 0, "botan": 0, "kasho": 0, "yuri": 0}

    def get_language(self, user_id: str) -> str:
        """ユーザーの言語設定を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            言語設定 ('ja' or 'en')、デフォルトは 'ja'
        """
        if not self.connected:
            if not self.connect():
                return 'ja'  # デフォルト: 日本語

        session = self.pg_manager.get_session(user_id)
        if session and 'language' in session:
            return session.get('language', 'ja')
        return 'ja'  # デフォルト: 日本語

    def toggle_language(self, user_id: str) -> str:
        """言語設定を切り替え（ja ↔ en）

        Args:
            user_id: LINEユーザーID

        Returns:
            切り替え後の言語 ('ja' or 'en')
        """
        if not self.connected:
            if not self.connect():
                return 'ja'

        # 現在の言語を取得
        current_language = self.get_language(user_id)

        # 言語を切り替え
        new_language = 'en' if current_language == 'ja' else 'ja'

        # セッションを更新
        session = self.pg_manager.get_session(user_id)
        current_character = session.get('selected_character') if session else None

        success = self.pg_manager.save_session(
            user_id=user_id,
            selected_character=current_character,
            last_message_at=datetime.now(),
            language=new_language
        )

        if success:
            logger.info(f"User {user_id[:8]}... toggled language: {current_language} -> {new_language}")
            return new_language
        else:
            logger.error(f"Failed to toggle language for user {user_id[:8]}...")
            return current_language

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()
