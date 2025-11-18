"""
User Memories Manager - ユーザー記憶管理システム

対話者について学んだことを記憶し、関係性を構築する
"""

import os
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
from .postgresql_manager import PostgreSQLManager
from .rag_search_system import RAGSearchSystem
from .fact_checker import FactChecker

logger = logging.getLogger(__name__)


class UserMemoriesManager:
    """user_memories 管理システム"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        self.rag_search = RAGSearchSystem(self.pg_manager)
        self.fact_checker = FactChecker()
        logger.info("✅ UserMemoriesManager初期化")

    def connect(self) -> bool:
        """PostgreSQL接続"""
        return self.rag_search.connect()

    def disconnect(self):
        """PostgreSQL切断"""
        self.rag_search.disconnect()

    async def extract_memories_from_conversation(
        self,
        user_message: str,
        bot_response: str,
        character: str
    ) -> List[Dict]:
        """
        会話から記憶を抽出（LLM使用）

        Args:
            user_message: ユーザーのメッセージ
            bot_response: ボットの応答
            character: キャラクター名

        Returns:
            [
                {
                    'memory_type': 'preference',
                    'memory_text': '犬アレルギー',
                    'context': '俺、犬アレルギーなんだよね',
                    'importance': 8,
                    'requires_fact_check': False
                },
                ...
            ]
        """
        # TODO: LLMを使って記憶を抽出する実装
        # 現時点では簡易的な実装
        memories = []

        # 基本的なパターンマッチング（仮実装）
        memory_patterns = {
            'preference': [
                ('好き', '嫌い', 'が好き', 'が嫌い'),
                ('愛してる', '大好き', '苦手')
            ],
            'fact': [
                ('アレルギー', '出身', '住んでる', '職業'),
                ('エンジニア', '学生', '社会人')
            ],
            'experience': [
                ('した', 'した事', 'に行った', 'を見た'),
                ('買った', '食べた', '会った')
            ]
        }

        # 簡易的な抽出（実際はLLMで行う）
        for memory_type, patterns_list in memory_patterns.items():
            for patterns in patterns_list:
                for pattern in patterns:
                    if pattern in user_message:
                        # パターンにマッチした場合、記憶として抽出
                        memories.append({
                            'memory_type': memory_type,
                            'memory_text': user_message,  # 仮: メッセージ全体
                            'context': user_message,
                            'importance': 5,
                            'requires_fact_check': False
                        })
                        break

        logger.info(f"💭 会話から{len(memories)}件の記憶を抽出")
        return memories

    def save_user_memory(
        self,
        user_id: str,
        character: str,
        memory_type: str,
        memory_text: str,
        context: str,
        importance: int = 5,
        confidence: float = 0.5,
        fact_checked: bool = False,
        fact_check_passed: Optional[bool] = None,
        fact_check_source: Optional[str] = None
    ) -> Optional[int]:
        """
        ユーザー記憶を保存

        Args:
            user_id: ユーザーID
            character: キャラクター名
            memory_type: 記憶タイプ ('preference', 'fact', 'experience', 'relationship', 'goal', 'emotion')
            memory_text: 記憶内容
            context: 元の会話文脈
            importance: 重要度 (1-10)
            confidence: 信頼度 (0.0-1.0)
            fact_checked: ファクトチェック済みか
            fact_check_passed: ファクトチェック結果
            fact_check_source: ファクトチェックのソース

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return None

        try:
            # embeddingを生成
            embedding = self.rag_search.generate_embedding(memory_text)

            if not embedding:
                logger.error("❌ embedding生成失敗")
                return None

            # embeddingをPostgreSQL配列形式に変換
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            with self.pg_manager.connection.cursor() as cursor:
                sql = """
                    INSERT INTO user_memories (
                        user_id, character, memory_type, memory_text, context,
                        embedding, importance, confidence,
                        fact_checked, fact_check_passed, fact_check_source,
                        learned_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s, NOW()
                    )
                    ON CONFLICT (user_id, character, memory_text) DO UPDATE SET
                        importance = EXCLUDED.importance,
                        confidence = EXCLUDED.confidence,
                        fact_checked = EXCLUDED.fact_checked,
                        fact_check_passed = EXCLUDED.fact_check_passed,
                        fact_check_source = EXCLUDED.fact_check_source,
                        reference_count = user_memories.reference_count + 1
                    RETURNING id
                """

                cursor.execute(sql, (
                    user_id, character, memory_type, memory_text, context,
                    embedding_str, importance, confidence,
                    fact_checked, fact_check_passed, fact_check_source
                ))

                memory_id = cursor.fetchone()[0]
                self.pg_manager.connection.commit()

                logger.info(f"✅ user_memory保存: ID={memory_id}, type={memory_type}, text={memory_text[:50]}")
                return memory_id

        except Exception as e:
            logger.error(f"❌ user_memory保存失敗: {e}")
            self.pg_manager.connection.rollback()
            return None

    async def extract_and_save(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        character: str
    ) -> int:
        """
        会話から記憶を抽出して保存

        Args:
            user_id: ユーザーID
            user_message: ユーザーのメッセージ
            bot_response: ボットの応答
            character: キャラクター名

        Returns:
            保存した記憶の件数
        """
        # 1. 記憶を抽出
        memories = await self.extract_memories_from_conversation(
            user_message,
            bot_response,
            character
        )

        if not memories:
            logger.debug("抽出された記憶なし")
            return 0

        # 2. 各記憶を保存
        saved_count = 0
        for memory in memories:
            # ファクトチェック（Phase 3）
            fact_check_result = None
            if memory.get('requires_fact_check', False):
                logger.info(f"🔍 ファクトチェック実行: {memory['memory_text'][:50]}...")
                fact_check_result = await self.fact_checker.check(memory['memory_text'])

                if not fact_check_result['passed']:
                    if fact_check_result['confidence'] == 0.0:
                        # 明らかに誤情報 → 保存しない
                        logger.warning(f"❌ 誤情報のため保存しない: {memory['memory_text'][:50]}")
                        logger.info(f"   正しくは: {fact_check_result.get('correct_info', '不明')}")
                        continue
                    else:
                        # 不明 → 低信頼度で保存
                        logger.info(f"⚠️ 確認できないため低信頼度で保存: {memory['memory_text'][:50]}")
                        memory['confidence'] = 0.3

            # 保存
            memory_id = self.save_user_memory(
                user_id=user_id,
                character=character,
                memory_type=memory['memory_type'],
                memory_text=memory['memory_text'],
                context=memory['context'],
                importance=memory.get('importance', 5),
                confidence=memory.get('confidence', 0.5),
                fact_checked=fact_check_result is not None,
                fact_check_passed=fact_check_result['passed'] if fact_check_result else None,
                fact_check_source='grok' if fact_check_result else None
            )

            if memory_id:
                saved_count += 1

        logger.info(f"💾 {saved_count}件の記憶を保存")
        return saved_count

    def search(
        self,
        user_id: str,
        character: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.6
    ) -> List[Dict]:
        """
        ユーザー記憶のRAG検索

        Args:
            user_id: ユーザーID
            character: キャラクター名
            query: 検索クエリ
            top_k: 上位何件取得するか
            similarity_threshold: 類似度の閾値

        Returns:
            [
                {
                    'memory_type': 'preference',
                    'memory_text': '犬アレルギー',
                    'context': '俺、犬アレルギーなんだよね',
                    'importance': 8,
                    'confidence': 0.9,
                    'learned_at': '2025-11-18 10:30:00',
                    'similarity': 0.92
                },
                ...
            ]
        """
        return self.rag_search.search_user_memories(
            user_id=user_id,
            character=character,
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

    def update_reference_count(self, memory_id: int) -> bool:
        """
        記憶の参照カウントを更新

        Args:
            memory_id: 記憶ID

        Returns:
            成功したらTrue
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.pg_manager.connection.cursor() as cursor:
                sql = """
                    UPDATE user_memories
                    SET reference_count = reference_count + 1,
                        last_referenced = NOW()
                    WHERE id = %s
                """
                cursor.execute(sql, (memory_id,))
                self.pg_manager.connection.commit()
                logger.debug(f"参照カウント更新: memory_id={memory_id}")
                return True

        except Exception as e:
            logger.error(f"❌ 参照カウント更新失敗: {e}")
            self.pg_manager.connection.rollback()
            return False

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()


# テスト用
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    # .envファイルを読み込み
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent.parent.parent / ".env")

    async def test_user_memories():
        """user_memories の基本動作テスト"""

        with UserMemoriesManager() as manager:
            # テストデータ
            user_id = "test_user_001"
            character = "yuri"

            # 1. 記憶を保存
            memory_id = manager.save_user_memory(
                user_id=user_id,
                character=character,
                memory_type="fact",
                memory_text="犬アレルギー",
                context="俺、犬アレルギーなんだよね",
                importance=8,
                confidence=0.9
            )

            print(f"\n✅ 記憶保存成功: ID={memory_id}")

            # 2. 検索テスト
            results = manager.search(
                user_id=user_id,
                character=character,
                query="犬飼ってる友達の家に行った",
                top_k=5,
                similarity_threshold=0.5
            )

            print(f"\n🔍 検索結果: {len(results)}件")
            for r in results:
                print(f"  - {r['memory_text']}: {r['context'][:50]}... (類似度: {r['similarity']:.2f})")

    # 実行
    asyncio.run(test_user_memories())
