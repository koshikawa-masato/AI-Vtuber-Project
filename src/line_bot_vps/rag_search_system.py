"""
RAG検索システム（PostgreSQL + pgvector版）

学習済み知識（learned_knowledgeテーブル）をセマンティック検索
"""

import os
import logging
from typing import List, Dict, Optional
from .postgresql_manager import PostgreSQLManager

logger = logging.getLogger(__name__)


class RAGSearchSystem:
    """RAG検索システム（PostgreSQL + pgvector）"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        self.connected = False
        logger.info("✅ RAG検索システム初期化（PostgreSQL + pgvector）")

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

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        OpenAI Embeddings API（text-embedding-3-small、$0.02/1M tokens）でembeddingを生成

        Args:
            text: テキスト

        Returns:
            embedding（1536次元ベクトル）
        """
        try:
            import openai

            openai.api_key = os.getenv('OPENAI_API_KEY')

            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"❌ Embeddings API Error: {e}")
            return None

    def search_learned_knowledge(
        self,
        character: str,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.6
    ) -> List[Dict]:
        """
        RAG検索: ユーザーの質問に意味的に近い学習済み知識を検索

        Args:
            character: キャラクター名
            query: ユーザーの質問
            top_k: 上位何件取得するか
            similarity_threshold: 類似度の閾値（デフォルト0.6）

        Returns:
            [
                {
                    'word': '単語',
                    'meaning': '意味',
                    'context': '文脈',
                    'similarity': 0.95
                },
                ...
            ]
        """
        # クエリのembeddingを生成
        query_embedding = self.generate_embedding(query)

        if not query_embedding:
            logger.error("❌ クエリのembedding生成失敗")
            return []

        if not self.connected:
            if not self.connect():
                logger.error("PostgreSQL未接続のため、RAG検索失敗")
                return []

        try:
            cursor = self.pg_manager.connection.cursor()

            # pgvectorのコサイン類似度検索（<=> 演算子）
            search_query = """
            SELECT
                word,
                meaning,
                context,
                1 - (embedding <=> %s::vector) as similarity
            FROM learned_knowledge
            WHERE character = %s AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """

            # embeddingをPostgreSQL配列形式に変換
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            cursor.execute(search_query, (
                embedding_str,
                character,
                embedding_str,
                top_k
            ))

            results = cursor.fetchall()

            # 結果を整形（閾値以上のみ）
            knowledge_list = []
            for row in results:
                word, meaning, context, similarity = row
                similarity_float = float(similarity)

                if similarity_float >= similarity_threshold:
                    knowledge_list.append({
                        'word': word,
                        'meaning': meaning,
                        'context': context,
                        'similarity': similarity_float
                    })
                    logger.info(f"📚 RAG検索ヒット: {word} (類似度: {similarity_float:.2f})")

            if knowledge_list:
                logger.info(f"✅ RAG検索: {len(knowledge_list)}件の関連知識を検出")
            else:
                logger.info(f"ℹ️ RAG検索: 類似度{similarity_threshold}以上の知識なし")

            return knowledge_list

        except Exception as e:
            logger.error(f"❌ RAG検索エラー: {e}")
            return []

    def search_user_memories(
        self,
        user_id: str,
        character: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.6
    ) -> List[Dict]:
        """
        RAG検索: ユーザーについて学んだ記憶を検索

        Args:
            user_id: ユーザーID
            character: キャラクター名
            query: ユーザーの質問
            top_k: 上位何件取得するか
            similarity_threshold: 類似度の閾値（デフォルト0.6）

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
        # クエリのembeddingを生成
        query_embedding = self.generate_embedding(query)

        if not query_embedding:
            logger.error("❌ クエリのembedding生成失敗")
            return []

        if not self.connected:
            if not self.connect():
                logger.error("PostgreSQL未接続のため、RAG検索失敗")
                return []

        try:
            cursor = self.pg_manager.connection.cursor()

            # pgvectorのコサイン類似度検索（<=> 演算子）
            search_query = """
            SELECT
                memory_type,
                memory_text,
                context,
                importance,
                confidence,
                learned_at,
                1 - (embedding <=> %s::vector) as similarity
            FROM user_memories
            WHERE user_id = %s AND character = %s AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """

            # embeddingをPostgreSQL配列形式に変換
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            cursor.execute(search_query, (
                embedding_str,
                user_id,
                character,
                embedding_str,
                top_k
            ))

            results = cursor.fetchall()

            # 結果を整形（閾値以上のみ）
            memory_list = []
            for row in results:
                memory_type, memory_text, context, importance, confidence, learned_at, similarity = row
                similarity_float = float(similarity)

                if similarity_float >= similarity_threshold:
                    memory_list.append({
                        'memory_type': memory_type,
                        'memory_text': memory_text,
                        'context': context,
                        'importance': importance,
                        'confidence': confidence,
                        'learned_at': str(learned_at),
                        'similarity': similarity_float
                    })
                    logger.info(f"💾 RAG検索ヒット（user_memories）: {memory_text} (類似度: {similarity_float:.2f})")

            if memory_list:
                logger.info(f"✅ user_memories RAG検索: {len(memory_list)}件の記憶を検出")
            else:
                logger.info(f"ℹ️ user_memories RAG検索: 類似度{similarity_threshold}以上の記憶なし")

            return memory_list

        except Exception as e:
            logger.error(f"❌ user_memories RAG検索エラー: {e}")
            return []

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

    # .envファイルを読み込み
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent.parent.parent / ".env")

    # RAG検索システムテスト
    with RAGSearchSystem() as rag:
        # 検索テスト
        results = rag.search_learned_knowledge(
            character="yuri",
            query="ネットスーパーのスキル持った異世界もののタイトルなんだっけ",
            top_k=5,
            similarity_threshold=0.6
        )

        print("\n検索結果:")
        for r in results:
            print(f"  - {r['word']}: {r['meaning'][:100]}... (類似度: {r['similarity']:.2f})")
