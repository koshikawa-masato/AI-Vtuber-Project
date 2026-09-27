"""
VPS用 FastAPI Webhook サーバー

- クラウドLLM（gpt-4o-mini）使用
- copy_robot_memory.db使用
- 学習ログ保存機能
- 30秒タイムアウト対応
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import hmac
import hashlib
import base64
import logging
from datetime import datetime
import os
import json
import time
import asyncio
# Note: MessageBuffer uses dict directly, not defaultdict
from dotenv import load_dotenv
from . import privacy_guard

# .envファイルを読み込み
load_dotenv()

from .cloud_llm_provider import CloudLLMProvider
from .learning_log_system_postgresql import LearningLogSystemPostgreSQL
from .session_manager_postgresql import SessionManagerPostgreSQL
from .postgresql_manager import PostgreSQLManager
from .rag_search_system import RAGSearchSystem
from .terms_flex_message import create_terms_flex_message
from .help_flex_message import create_help_flex_message
from .stats_flex_message import create_stats_flex_message
from .feedback_notifier import FeedbackNotifier
from .auto_character_selector import AutoCharacterSelector
from .integrated_judgment_engine import IntegratedJudgmentEngine
from .adaptive_response_generator import AdaptiveResponseGenerator
from .user_memories_manager import UserMemoriesManager

# 既存のモジュールを活用
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.prompt_manager import PromptManager

# ロギング設定（日次ローテーション）
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# ログディレクトリ作成
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "line_bot_vps.log"

# ロガー設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# フォーマッター
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 日次ローテーションハンドラー
file_handler = TimedRotatingFileHandler(
    filename=str(LOG_FILE),
    when='midnight',      # 毎日0時にローテーション
    interval=1,           # 1日ごと
    backupCount=7,        # 7日分保持
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.suffix = "%Y-%m-%d"  # ローテート後のファイル名: line_bot_vps.log.2025-11-17

# コンソールハンドラー（開発用）
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# ハンドラー追加
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ルートロガーも設定（他のモジュールのログも記録）
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


# ========================================
# メッセージバッファリング（連続メッセージ結合）
# ========================================
class MessageBuffer:
    """
    短時間に連続送信されたメッセージを結合する。

    LINEユーザーは「今日」「バイト」「疲れた」のように
    複数の短いメッセージを連続で送ることが多い。
    これらを1つのメッセージとして処理することで、
    より自然な応答が可能になる。
    """

    def __init__(self, buffer_timeout: float = 1.5):
        """
        Args:
            buffer_timeout: メッセージを待つ時間（秒）
        """
        self.buffer_timeout = buffer_timeout
        self.buffers = {}  # user_id -> {"messages": [], "last_time": float, "task": asyncio.Task}
        self.callbacks = {}  # user_id -> callback function
        self._lock = asyncio.Lock()

    async def add_message(
        self,
        user_id: str,
        message: str,
        reply_token: str,
        callback
    ) -> bool:
        """
        メッセージをバッファに追加。

        Args:
            user_id: ユーザーID
            message: メッセージ内容
            reply_token: LINE返信トークン（最新のものを使用）
            callback: バッファフラッシュ時に呼ばれるコールバック

        Returns:
            True: バッファに追加された（まだ処理しない）
            False: 即座に処理すべき（特殊コマンドなど）
        """
        # 特殊コマンドは即座に処理（バッファリングしない）
        special_commands = ["ヘルプ", "help", "利用規約", "メニュー", "キャラ変更", "統計"]
        if any(cmd in message.lower() for cmd in special_commands):
            return False

        async with self._lock:
            now = time.time()

            if user_id in self.buffers:
                # 既存バッファに追加
                buf = self.buffers[user_id]
                buf["messages"].append(message)
                buf["last_time"] = now
                buf["reply_token"] = reply_token  # 最新のトークンを保持

                # 既存のタイマータスクをキャンセル
                if buf.get("task") and not buf["task"].done():
                    buf["task"].cancel()

                # 新しいタイマーを開始
                buf["task"] = asyncio.create_task(
                    self._flush_after_timeout(user_id)
                )

                logger.info(f"📝 バッファ追加: {user_id[:8]}... ({len(buf['messages'])}件)")
                return True
            else:
                # 新規バッファ作成
                self.buffers[user_id] = {
                    "messages": [message],
                    "last_time": now,
                    "reply_token": reply_token,
                    "task": None
                }
                self.callbacks[user_id] = callback

                # タイマー開始
                self.buffers[user_id]["task"] = asyncio.create_task(
                    self._flush_after_timeout(user_id)
                )

                logger.info(f"📝 バッファ開始: {user_id[:8]}...")
                return True

    async def _flush_after_timeout(self, user_id: str):
        """タイムアウト後にバッファをフラッシュ"""
        await asyncio.sleep(self.buffer_timeout)
        await self.flush(user_id)

    async def flush(self, user_id: str):
        """バッファをフラッシュして結合メッセージを処理"""
        async with self._lock:
            if user_id not in self.buffers:
                return

            buf = self.buffers.pop(user_id)
            callback = self.callbacks.pop(user_id, None)

        if not buf["messages"]:
            return

        # メッセージを結合（スペースで区切る）
        combined_message = " ".join(buf["messages"])

        logger.info(f"📤 バッファフラッシュ: {user_id[:8]}... -> \"{combined_message[:50]}...\"")

        # コールバック実行
        if callback:
            try:
                await callback(
                    user_id=user_id,
                    combined_message=combined_message,
                    reply_token=buf["reply_token"],
                    message_count=len(buf["messages"])
                )
            except Exception as e:
                logger.error(f"❌ バッファコールバックエラー: {e}")

    def get_buffer_status(self, user_id: str) -> dict:
        """バッファの状態を取得（デバッグ用）"""
        if user_id in self.buffers:
            buf = self.buffers[user_id]
            return {
                "message_count": len(buf["messages"]),
                "messages": buf["messages"],
                "waiting_seconds": time.time() - buf["last_time"]
            }
        return {"message_count": 0, "messages": [], "waiting_seconds": 0}


# グローバルなメッセージバッファ（1.5秒待機）
message_buffer = MessageBuffer(buffer_timeout=1.5)
logger.info("✅ MessageBuffer初期化完了（1.5秒バッファリング）")


# FastAPIアプリ作成
app = FastAPI(
    title="牡丹プロジェクト VPS LINE Bot API",
    description="VPS用 クラウドLLM + 学習ログシステム",
    version="0.1.0"
)

# 静的ファイル（アイコン画像）を配信
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
app.mount("/assets", StaticFiles(directory=str(project_root / "assets")), name="assets")

# ========================================
# 設定
# ========================================

# LINE Channel Secret（環境変数から取得）
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    logger.warning("⚠️ LINE認証情報が設定されていません")

# クラウドLLM初期化（環境変数から設定取得）
VPS_LLM_PROVIDER = os.getenv("VPS_LLM_PROVIDER", "openai")
VPS_LLM_MODEL = os.getenv("VPS_LLM_MODEL", "gpt-4o-mini")

llm_provider = CloudLLMProvider(
    provider=VPS_LLM_PROVIDER,
    model=VPS_LLM_MODEL,
    temperature=0.7,
    max_tokens=500
)
logger.info(f"✅ CloudLLMProvider初期化完了（{VPS_LLM_PROVIDER}: {VPS_LLM_MODEL}）")

# グローバルなPostgreSQLManager（VPS内localhost接続）
pg_manager = PostgreSQLManager()
logger.info("✅ PostgreSQLManager初期化完了")

# 学習ログシステム初期化（PostgreSQL版）
learning_log_system = LearningLogSystemPostgreSQL(pg_manager=pg_manager)
logger.info("✅ LearningLogSystemPostgreSQL初期化完了")

# セッション管理システム初期化（PostgreSQL版）
session_manager = SessionManagerPostgreSQL(pg_manager=pg_manager)
logger.info("✅ SessionManagerPostgreSQL初期化完了")

# プロンプト管理システム初期化
prompt_manager = PromptManager()
logger.info("✅ PromptManager初期化完了")

# フィードバック通知システム初期化（Messaging API）
feedback_notifier = FeedbackNotifier(channel_access_token=CHANNEL_ACCESS_TOKEN)
logger.info("✅ FeedbackNotifier初期化完了（Messaging API）")

# 三姉妹自動選択システム初期化
auto_character_selector = AutoCharacterSelector(mysql_manager=pg_manager)
logger.info("✅ AutoCharacterSelector初期化完了")

# RAG検索システム初期化（PostgreSQL + pgvector）
rag_search_system = RAGSearchSystem(pg_manager=pg_manager)
logger.info("✅ RAGSearchSystem初期化完了（PostgreSQL + pgvector）")

# 統合判定エンジン初期化（7層防御）
integrated_judgment_engine = IntegratedJudgmentEngine(pg_manager=pg_manager)
logger.info("✅ IntegratedJudgmentEngine初期化完了（7層防御）")

# 臨機応変な応答生成システム初期化
adaptive_response_generator = AdaptiveResponseGenerator()
logger.info("✅ AdaptiveResponseGenerator初期化完了")

# ユーザー記憶管理システム初期化
user_memories_manager = UserMemoriesManager(pg_manager=pg_manager)
logger.info("✅ UserMemoriesManager初期化完了")

# ========================================
# アプリケーションライフサイクル
# ========================================

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("=" * 60)
    logger.info("🚀 VPS LINE Bot起動")
    logger.info(f"   LLM: {VPS_LLM_PROVIDER}/{VPS_LLM_MODEL}")
    logger.info(f"   学習ログDB: PostgreSQL (localhost)")
    logger.info(f"   キャラクター: {', '.join(CHARACTERS.keys())}")
    logger.info("=" * 60)

    # PostgreSQL接続（VPS内localhost接続）
    if pg_manager.connect():
        logger.info("🎉 PostgreSQL接続成功（localhost）")
        # RAG検索システムもpg_managerを共有しているため自動的に使用可能
        rag_search_system.connect()
        logger.info("✅ RAG検索システム接続完了")
        # 統合判定エンジンもpg_managerを共有
        integrated_judgment_engine.connect()
        logger.info("✅ 統合判定エンジン接続完了")
        # ユーザー記憶管理システムもpg_managerを共有
        user_memories_manager.connect()
        logger.info("✅ ユーザー記憶管理システム接続完了")
    else:
        logger.error("❌ PostgreSQL接続失敗")

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("👋 VPS LINE Bot終了")
    # PostgreSQL切断
    user_memories_manager.disconnect()
    integrated_judgment_engine.disconnect()
    rag_search_system.disconnect()
    pg_manager.disconnect()
    logger.info("👋 PostgreSQL接続を切断しました")

# ========================================
# キャラクター設定
# ========================================

# キャラクター設定
ICON_BASE_URL = "https://www.three-sisters.ai/images"
CHARACTERS = {
    "kasho": {
        "name": "Kasho",
        "display_name": "Kasho（花相）",
        "age": 19,
        "icon_url": f"{ICON_BASE_URL}/kasho_icon.jpg"
    },
    "botan": {
        "name": "牡丹",
        "display_name": "牡丹（Botan）",
        "age": 17,
        "icon_url": f"{ICON_BASE_URL}/botan_icon.jpg"
    },
    "yuri": {
        "name": "ユリ",
        "display_name": "ユリ（Yuri）",
        "age": 15,
        "icon_url": f"{ICON_BASE_URL}/yuri_icon.jpg"
    }
}

# ========================================
# ヘルパー関数
# ========================================

def verify_signature(body: bytes, signature: str) -> bool:
    """
    LINE署名検証

    Args:
        body: リクエストボディ
        signature: X-Line-Signature

    Returns:
        検証結果
    """
    hash_digest = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(hash_digest).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)


async def generate_response(
    character: str,
    user_message: str,
    user_id: str,
    conversation_history: Optional[list] = None
) -> tuple[str, float]:
    """
    応答生成（統合判定エンジン統合版）

    Args:
        character: キャラクター名
        user_message: ユーザーメッセージ
        user_id: ユーザーID
        conversation_history: 会話履歴 [{"role": "user", "content": "..."}, ...]

    Returns:
        (応答テキスト, 処理時間)
    """
    start_time = time.time()

    try:
        # 統合判定（7層防御）
        judgment = None
        try:
            judgment = await integrated_judgment_engine.judge(
                user_message=user_message,
                user_id=user_id,
                character=character
            )
            logger.info(f"🛡️ 統合判定完了: playful={judgment['playful']['is_playful']}, "
                       f"sensitive={judgment['sensitive']['level']}")
        except Exception as e:
            logger.warning(f"⚠️ 統合判定失敗（スキップ）: {e}")

        # 言語設定を取得
        language = session_manager.get_language(user_id)
        logger.info(f"🌐 ユーザー言語設定: {language}")

        # プロンプト取得（世界観ルール + キャラクタープロンプト）
        character_prompt = prompt_manager.get_combined_prompt(character)

        # 応答スタイル指示を追加（個性に基づく）
        if judgment:
            style_instruction = adaptive_response_generator.get_response_style_instruction(
                judgment['personality']
            )
            character_prompt += f"\n\n{style_instruction}"

        # TODO: Phase D記憶検索統合（copy_robot_memory.dbから）
        memories = None  # 将来的に実装

        # RAG検索: 学習済み知識を検索（類似度0.6以上）
        learned_knowledge = []
        try:
            learned_knowledge = rag_search_system.search_learned_knowledge(
                character=character,
                query=user_message,
                top_k=5,
                similarity_threshold=0.6
            )

            # RAG検索結果をプロンプトに追加
            if learned_knowledge:
                logger.info(f"📚 RAG: {len(learned_knowledge)}件の関連知識を検出")
                rag_context = "\n\n【参考知識（過去に学習した情報）】\n"
                for k in learned_knowledge:
                    rag_context += f"- {k['word']}: {k['meaning']}\n"

                # システムプロンプトにRAG情報を追加
                character_prompt += rag_context
        except Exception as e:
            logger.warning(f"⚠️ RAG検索失敗（スキップ）: {e}")

        # RAG検索: ユーザー記憶を検索
        user_memories = []
        try:
            user_memories = user_memories_manager.search(
                user_id=user_id,
                character=character,
                query=user_message,
                top_k=5,
                similarity_threshold=0.6
            )

            # ユーザー記憶をプロンプトに追加
            if user_memories:
                logger.info(f"💾 user_memories: {len(user_memories)}件のユーザー記憶を検出")
                user_context = "\n\n【このユーザーについて覚えていること】\n"
                for m in user_memories:
                    user_context += f"- {m['memory_text']}\n"

                # システムプロンプトにユーザー記憶を追加
                character_prompt += user_context
        except Exception as e:
            logger.warning(f"⚠️ user_memories検索失敗（スキップ）: {e}")

        # 今日のトレンド情報を取得（PostgreSQLから）※グローバルpg_managerを使用
        daily_trends = None
        try:
            if pg_manager.connection or pg_manager.connect():
                daily_trends = pg_manager.get_recent_trends(character=character, limit=3)
                if daily_trends:
                    logger.info(f"✅ トレンド情報取得: {len(daily_trends)}件")
        except Exception as e:
            logger.warning(f"⚠️ トレンド情報取得失敗（スキップ）: {e}")

        # 適応的応答生成（プロレス・誤情報への対応）
        adaptive_response = None
        if judgment:
            try:
                adaptive_response = await adaptive_response_generator.generate(
                    user_message=user_message,
                    judgment=judgment,
                    character=character
                )
            except Exception as e:
                logger.warning(f"⚠️ 適応的応答生成失敗（スキップ）: {e}")

        # 適応的応答がある場合はそれを返す
        if adaptive_response:
            logger.info(f"💬 適応的応答を使用")
            response = adaptive_response
        else:
            # LLM生成（会話履歴 + トレンド情報 + 言語設定を含む）
            response = llm_provider.generate_with_context(
                user_message=user_message,
                character_name=CHARACTERS[character]["name"],
                character_prompt=character_prompt,
                memories=memories,
                daily_trends=daily_trends,
                conversation_history=conversation_history,
                metadata={
                    "user_id": user_id,
                    "character": character,
                    "platform": "LINE_VPS"
                },
                language=language
            )

        # 応答後処理: 個性更新 + 記憶保存
        if judgment:
            try:
                # 個性を更新
                await integrated_judgment_engine.update_personality_from_judgment(
                    user_id=user_id,
                    judgment=judgment,
                    interaction_positive=True  # TODO: 応答の評価
                )

                # ユーザー記憶を抽出・保存
                await user_memories_manager.extract_and_save(
                    user_id=user_id,
                    user_message=user_message,
                    bot_response=response,
                    character=character
                )
            except Exception as e:
                logger.warning(f"⚠️ 応答後処理失敗（スキップ）: {e}")

        elapsed_time = time.time() - start_time

        logger.info(f"✅ 応答生成完了: {elapsed_time:.2f}秒")

        return response, elapsed_time

    except Exception as e:
        logger.error(f"❌ 応答生成エラー: {e}")
        elapsed_time = time.time() - start_time
        return "ごめんね、ちょっと調子が悪いみたい...また後で話そう？", elapsed_time


# ========================================
# エンドポイント
# ========================================

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "VPS LINE Bot",
        "version": "0.1.0",
        "llm": "gpt-4o-mini"
    }


@app.get("/api/stats")
async def get_stats():
    """学習ログ統計情報取得"""
    try:
        stats = learning_log_system.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"❌ 統計情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning-logs")
async def get_learning_logs(
    since: Optional[str] = None,
    character: Optional[str] = None,
    limit: int = 100
):
    """
    学習ログ取得（開発者用API）

    Args:
        since: この日時以降のログを取得（ISO format）
        character: 特定のキャラクターのみ取得
        limit: 最大取得件数
    """
    try:
        logs = learning_log_system.get_logs(
            since=since,
            character=character,
            limit=limit
        )
        return JSONResponse(content={"logs": logs, "count": len(logs)})
    except Exception as e:
        logger.error(f"❌ 学習ログ取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Push Message API（バッファリング用）
# ========================================
def send_push_message(user_id: str, text: str, character: str) -> bool:
    """
    LINE Push Message API を使用してメッセージを送信。

    バッファリングされたメッセージはreply_tokenが期限切れになるため、
    Push APIを使用する。

    Args:
        user_id: LINE ユーザーID
        text: 送信するテキスト
        character: キャラクター名（アイコン設定用）

    Returns:
        成功したらTrue
    """
    import requests

    push_url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": text,
                "sender": {
                    "name": CHARACTERS[character]["display_name"],
                    "iconUrl": CHARACTERS[character]["icon_url"]
                }
            }
        ]
    }

    try:
        response = requests.post(push_url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.info(f"✅ Push送信成功: {character} -> {text[:30]}...")
            return True
        else:
            logger.error(f"❌ Push送信エラー: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Push API呼び出しエラー: {e}")
        return False


async def process_combined_message(
    user_id: str,
    combined_message: str,
    reply_token: str,
    message_count: int
):
    """
    バッファから結合されたメッセージを処理するコールバック。

    Args:
        user_id: LINE ユーザーID
        combined_message: 結合されたメッセージ
        reply_token: LINE返信トークン（期限切れの可能性あり）
        message_count: 結合されたメッセージ数
    """
    logger.info(f"🔄 結合メッセージ処理開始: {user_id[:8]}... ({message_count}件結合)")

    try:
        # モード取得（auto / botan / kasho / yuri）
        selected_mode = pg_manager.get_user_mode(user_id)

        if selected_mode == "auto":
            # 自動モード: 三姉妹で親和性スコアリング
            selection_result = auto_character_selector.select_best_character(combined_message)
            character = selection_result["character"]
            scores = selection_result["scores"]
            logger.info(f"🎯 自動選択: {character} (スコア: {scores})")
        else:
            # 固定モード
            character = selected_mode
            logger.info(f"📌 固定モード: {character}")

        # 会話履歴を取得（過去30件）
        conversation_history = session_manager.get_conversation_history(
            user_id=user_id,
            character=character,
            limit=30
        )
        if conversation_history:
            logger.info(f"📚 会話履歴取得: {len(conversation_history)}件")

        # 応答生成
        bot_response, response_time = await generate_response(
            character=character,
            user_message=combined_message,
            user_id=user_id,
            conversation_history=conversation_history
        )

        # 会話履歴を保存
        try:
            success = session_manager.save_conversation(
                user_id=user_id,
                character=character,
                user_message=combined_message,
                bot_response=bot_response
            )
            if success:
                logger.debug(f"💾 会話履歴保存完了")
            else:
                logger.error(f"❌ 会話履歴保存失敗")
        except Exception as e:
            logger.error(f"❌ 会話履歴保存エラー: {e}")

        # 学習ログ保存
        try:
            learning_log_system.save_log(
                character=character,
                user_id=user_id,
                user_message=combined_message,
                bot_response=bot_response,
                response_time=response_time
            )
        except Exception as e:
            logger.error(f"❌ 学習ログ保存エラー: {e}")

        # 最終メッセージ時刻を更新
        session_manager.update_last_message_time(user_id, character)

        # Push APIで返信（reply_tokenは期限切れの可能性があるため）
        send_push_message(user_id, bot_response, character)

    except Exception as e:
        logger.error(f"❌ 結合メッセージ処理エラー: {e}")
        # エラー時もユーザーに通知
        try:
            send_push_message(user_id, "ごめんね、ちょっとエラーが起きちゃった...もう一度話しかけてくれる？", "botan")
        except Exception:
            pass


@app.post("/webhook")
async def webhook(request: Request):
    """
    LINE Webhook エンドポイント（単一・キャラクター選択対応）
    """
    # リクエストボディ取得
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 署名検証（本番環境のみ）
    if CHANNEL_SECRET and not verify_signature(body, signature):
        logger.warning("⚠️ 署名検証失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # JSON解析
    try:
        webhook_data = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # イベント処理
    events = webhook_data.get("events", [])

    for event in events:
        event_type = event.get("type")
        user_id = event.get("source", {}).get("userId", "unknown")
        reply_token = event.get("replyToken")

        # 友だち登録イベント処理（ウェルカムメッセージ）
        if event_type == "follow":
            logger.info(f"👋 新規友だち登録: {user_id[:8]}...")

            try:
                import requests
                welcome_message = (
                    "👋 友だち登録ありがとうございます！\n\n"
                    "牡丹プロジェクトへようこそ！\n"
                    "三姉妹（牡丹・Kasho・ユリ）とお話しできるよ。\n\n"
                    "⚠️ 【重要なお知らせ】\n"
                    "・テキストメッセージのみ対応しています\n"
                    "・スタンプや画像は無視されます\n\n"
                    "📱 まずは下のメニューから\n"
                    "「キャラクター選択」をタップして\n"
                    "話したいキャラクターを選んでね！\n\n"
                    "利用規約・免責事項は\n"
                    "メニューの「利用規約」から確認できます。"
                )

                reply_url = "https://api.line.me/v2/bot/message/reply"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                }
                payload = {
                    "replyToken": reply_token,
                    "messages": [{
                        "type": "text",
                        "text": welcome_message
                    }]
                }
                response = requests.post(reply_url, headers=headers, json=payload)

                if response.status_code == 200:
                    logger.info(f"✅ ウェルカムメッセージ送信成功: {user_id[:8]}...")
                else:
                    logger.error(f"❌ ウェルカムメッセージ送信エラー: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"❌ ウェルカムメッセージ処理エラー: {e}")

        # Postbackイベント処理（キャラクター選択・メニューアクション）
        elif event_type == "postback":
            postback_data = event.get("postback", {}).get("data", "")
            logger.info(f"📲 Postback受信: {postback_data}")

            # キャラクター選択処理
            if postback_data.startswith("character="):
                character = postback_data.split("=")[1]
                if character in CHARACTERS:
                    # キャラクターを設定
                    session_manager.set_character(user_id, character)

                    # 言語を切り替え（JP ↔ EN）
                    new_language = session_manager.toggle_language(user_id)

                    # バイリンガル確認メッセージ（言語コード表示）
                    if new_language == 'en':
                        reply_message = f"✨ You selected {CHARACTERS[character]['display_name']}! (Lang: EN)\n✨ {CHARACTERS[character]['display_name']}を選択したよ！（Lang: EN）"
                    else:
                        reply_message = f"✨ {CHARACTERS[character]['display_name']}を選択したよ！（Lang: JA）\n✨ You selected {CHARACTERS[character]['display_name']}! (Lang: JA)"

                    try:
                        import requests
                        reply_url = "https://api.line.me/v2/bot/message/reply"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                        }
                        payload = {
                            "replyToken": reply_token,
                            "messages": [{
                                "type": "text",
                                "text": reply_message,
                                "sender": {
                                    "name": CHARACTERS[character]["display_name"],
                                    "iconUrl": CHARACTERS[character]["icon_url"]
                                }
                            }]
                        }
                        response = requests.post(reply_url, headers=headers, json=payload)

                        if response.status_code == 200:
                            logger.info(f"✅ キャラクター選択返信成功: {character}, language={new_language}")
                        else:
                            logger.error(f"❌ 返信エラー: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # モード設定処理（自動/固定）- スマート切り替えロジック
            elif postback_data.startswith("action=set_mode&mode="):
                mode = postback_data.split("mode=")[1]
                if mode in ["auto", "botan", "kasho", "yuri"]:
                    # 現在のモードを取得
                    session = pg_manager.get_session(user_id)
                    current_mode = session.get('selected_mode') if session else None

                    if mode == current_mode:
                        # 同じモード → 言語を切り替え（モードは変更しない）
                        new_language = session_manager.toggle_language(user_id)

                        # 言語切り替え確認メッセージ（バイリンガル）
                        if new_language == 'en':
                            reply_message = (
                                "🌐 Language switched to English! (Lang: EN)\n"
                                "🌐 言語を英語に切り替えました！（Lang: EN）"
                            )
                        else:
                            reply_message = (
                                "🌐 言語を日本語に切り替えました！（Lang: JA）\n"
                                "🌐 Language switched to Japanese! (Lang: JA)"
                            )
                    else:
                        # 異なるモード → モードを変更（言語は変更しない）
                        pg_manager.set_user_mode(user_id, mode)
                        current_language = session_manager.get_language(user_id)
                        lang_code = current_language.upper()

                        # モード別確認メッセージ（バイリンガル + 言語コード表示）
                        if mode == "auto":
                            if current_language == 'en':
                                reply_message = (
                                    f"✅ Set to Auto mode! (Lang: {lang_code})\n"
                                    f"✅ 自動モードに設定しました！（Lang: {lang_code}）\n\n"
                                    f"The three sisters will respond based on the topic:\n"
                                    f"🌸 Botan: VTuber, Entertainment\n"
                                    f"🎵 Kasho: Music, Audio\n"
                                    f"📚 Yuri: Subculture, Anime, Light Novels"
                                )
                            else:
                                reply_message = (
                                    f"✅ 自動モードに設定しました！（Lang: {lang_code}）\n"
                                    f"✅ Set to Auto mode! (Lang: {lang_code})\n\n"
                                    f"これからは、話題に合わせて三姉妹が自動的に応答します：\n"
                                    f"🌸 牡丹: VTuber、エンタメ\n"
                                    f"🎵 Kasho: 音楽、オーディオ\n"
                                    f"📚 ユリ: サブカル、アニメ、ライトノベル"
                                )
                        elif mode == "botan":
                            if current_language == 'en':
                                reply_message = (
                                    f"✨ You selected 牡丹 (Botan)! (Lang: {lang_code})\n"
                                    f"✨ 牡丹に固定しました！（Lang: {lang_code}）"
                                )
                            else:
                                reply_message = (
                                    f"✨ 牡丹に固定しました！（Lang: {lang_code}）\n"
                                    f"✨ You selected 牡丹 (Botan)! (Lang: {lang_code})"
                                )
                        elif mode == "kasho":
                            if current_language == 'en':
                                reply_message = (
                                    f"✨ You selected Kasho (花相)! (Lang: {lang_code})\n"
                                    f"✨ Kashoに固定しました！（Lang: {lang_code}）"
                                )
                            else:
                                reply_message = (
                                    f"✨ Kashoに固定しました！（Lang: {lang_code}）\n"
                                    f"✨ You selected Kasho (花相)! (Lang: {lang_code})"
                                )
                        elif mode == "yuri":
                            if current_language == 'en':
                                reply_message = (
                                    f"✨ You selected ユリ (Yuri)! (Lang: {lang_code})\n"
                                    f"✨ ユリに固定しました！（Lang: {lang_code}）"
                                )
                            else:
                                reply_message = (
                                    f"✨ ユリに固定しました！（Lang: {lang_code}）\n"
                                    f"✨ You selected ユリ (Yuri)! (Lang: {lang_code})"
                                )

                    try:
                        import requests
                        reply_url = "https://api.line.me/v2/bot/message/reply"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                        }
                        payload = {
                            "replyToken": reply_token,
                            "messages": [{
                                "type": "text",
                                "text": reply_message
                            }]
                        }
                        response = requests.post(reply_url, headers=headers, json=payload)

                        if response.status_code == 200:
                            logger.info(f"✅ モード設定返信成功: {mode}")
                        else:
                            logger.error(f"❌ 返信エラー: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # 自動モード設定（リッチメニューの「自動」ボタン）
            elif postback_data == "action=auto":
                # 自動モードに設定
                pg_manager.set_user_mode(user_id, "auto")
                current_language = session_manager.get_language(user_id)
                lang_code = current_language.upper()

                if current_language == 'en':
                    reply_message = (
                        f"✅ Set to Auto mode! (Lang: {lang_code})\n"
                        f"✅ 自動モードに設定しました！（Lang: {lang_code}）\n\n"
                        f"The three sisters will respond based on the topic:\n"
                        f"🌸 Botan: VTuber, Entertainment\n"
                        f"🎵 Kasho: Music, Audio\n"
                        f"📚 Yuri: Subculture, Anime, Light Novels"
                    )
                else:
                    reply_message = (
                        f"✅ 自動モードに設定しました！（Lang: {lang_code}）\n"
                        f"✅ Set to Auto mode! (Lang: {lang_code})\n\n"
                        f"これからは、話題に合わせて三姉妹が自動的に応答します：\n"
                        f"🌸 牡丹: VTuber、エンタメ\n"
                        f"🎵 Kasho: 音楽、オーディオ\n"
                        f"📚 ユリ: サブカル、アニメ、ライトノベル"
                    )

                try:
                    import requests
                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{
                            "type": "text",
                            "text": reply_message
                        }]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ 自動モード設定成功")
                    else:
                        logger.error(f"❌ 返信エラー: {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # フィードバック受付
            elif postback_data == "action=feedback":
                pg_manager.set_feedback_state(user_id, "waiting")

                # 言語設定を取得
                language = session_manager.get_language(user_id)

                # バイリンガルメッセージ
                if language == 'en':
                    reply_message = (
                        "📝 We're waiting for your feedback!\n\n"
                        "Please send us:\n"
                        "- Bug reports\n"
                        "- Feature requests\n"
                        "- Improvement suggestions\n"
                        "- Other comments\n\n"
                        "Enter your feedback in the next message."
                    )
                    cancel_label = "❌ Cancel"
                    cancel_text = "Cancel"
                else:
                    reply_message = (
                        "📝 フィードバックをお待ちしています！\n\n"
                        "以下のような内容をお送りください：\n"
                        "- バグ報告\n"
                        "- 機能要望\n"
                        "- 改善提案\n"
                        "- その他ご意見\n\n"
                        "次のメッセージでフィードバックを入力してください。"
                    )
                    cancel_label = "❌ キャンセル"
                    cancel_text = "キャンセル"

                try:
                    import requests
                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{
                            "type": "text",
                            "text": reply_message,
                            "quickReply": {
                                "items": [
                                    {
                                        "type": "action",
                                        "action": {
                                            "type": "message",
                                            "label": cancel_label,
                                            "text": cancel_text
                                        }
                                    }
                                ]
                            }
                        }]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ フィードバック受付返信成功 (language={language})")
                    else:
                        logger.error(f"❌ 返信エラー: {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # 利用規約表示
            elif postback_data == "action=terms":
                try:
                    import requests
                    # 言語設定を取得
                    language = session_manager.get_language(user_id)

                    # TODO: 将来的にバイリンガルFlex Messageを作成
                    flex_message = create_terms_flex_message()
                    alt_text = "Terms of Service" if language == 'en' else "利用規約・免責事項"

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "flex", "altText": alt_text, "contents": flex_message}]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ 利用規約返信成功 (language={language})")
                    else:
                        logger.error(f"❌ 返信エラー: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"❌ 利用規約表示エラー: {e}")

            # ヘルプ表示
            elif postback_data == "action=help":
                try:
                    import requests
                    # 言語設定を取得
                    language = session_manager.get_language(user_id)

                    # TODO: 将来的にバイリンガルFlex Messageを作成
                    flex_message = create_help_flex_message()
                    alt_text = "Help" if language == 'en' else "ヘルプ・使い方"

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "flex", "altText": alt_text, "contents": flex_message}]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ ヘルプ返信成功 (language={language})")
                    else:
                        logger.error(f"❌ ヘルプ返信エラー: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"❌ ヘルプ表示エラー: {e}")

            # 統計表示
            elif postback_data == "action=stats":
                try:
                    import requests
                    # ユーザーの会話統計を取得
                    current_character = session_manager.get_character_or_default(user_id, default=None)
                    stats = session_manager.get_user_stats(user_id)

                    logger.info(f"📊 統計取得: total={stats['total']}, botan={stats['botan']}, kasho={stats['kasho']}, yuri={stats['yuri']}")

                    flex_message = create_stats_flex_message(
                        total_messages=stats['total'],
                        botan_count=stats['botan'],
                        kasho_count=stats['kasho'],
                        yuri_count=stats['yuri'],
                        current_character=current_character
                    )

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "flex", "altText": "あなたの統計", "contents": flex_message}]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ 統計返信成功")
                    else:
                        logger.error(f"❌ 統計返信エラー: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"❌ 統計表示エラー: {e}")

        # メッセージイベント処理
        elif event_type == "message":
            message_type = event.get("message", {}).get("type")

            if message_type == "text":
                # テキストメッセージ処理
                user_message = event.get("message", {}).get("text", "")
                privacy_result = await asyncio.to_thread(privacy_guard.screen, user_message)
                if privacy_result.blocked:
                    notice = ("安全性を確認できないため、このメッセージの処理を保留しました。"
                              if privacy_result.review_required else "個人情報を含むため、このメッセージは処理できません。")
                    await asyncio.to_thread(send_push_message, user_id, notice, "botan")
                    continue

                # フィードバック待ち状態の確認
                feedback_state = pg_manager.get_feedback_state(user_id)

                # 「キャンセル」のみの入力は無視（フィードバック待ちでなくても反応しない）
                if user_message.lower() in ["キャンセル", "cancel"]:
                    if feedback_state == "waiting":
                        # フィードバック待ち中のキャンセル
                        pg_manager.set_feedback_state(user_id, "none")
                        bot_response = "フィードバックをキャンセルしました。"
                        # LINE返信
                        try:
                            import requests
                            reply_url = "https://api.line.me/v2/bot/message/reply"
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                            }
                            payload = {
                                "replyToken": reply_token,
                                "messages": [{
                                    "type": "text",
                                    "text": bot_response
                                }]
                            }
                            response = requests.post(reply_url, headers=headers, json=payload)
                            if response.status_code == 200:
                                logger.info(f"✅ フィードバックキャンセル完了")
                            else:
                                logger.error(f"❌ 返信エラー: {response.status_code}")
                        except Exception as e:
                            logger.error(f"❌ LINE API呼び出しエラー: {e}")
                    else:
                        # フィードバック待ちでない場合は無視
                        logger.info(f"🔇 キャンセル入力を無視（フィードバック待ちでない）")
                    continue  # 次のイベントへ

                if feedback_state == "waiting":
                    # フィードバック処理（キャンセル以外）
                    # フィードバック保存
                    pg_manager.save_feedback(user_id, user_message)
                    pg_manager.set_feedback_state(user_id, "none")

                    # Messaging API で開発者に通知
                    feedback_notifier.send_feedback_notification(user_id, user_message)

                    bot_response = (
                        "✅ フィードバックを受け付けました！\n"
                        "ありがとうございます！\n\n"
                        "開発者に通知しました。\n"
                        "今後の改善に活かさせていただきます。"
                    )

                    # LINE返信
                    try:
                        import requests
                        reply_url = "https://api.line.me/v2/bot/message/reply"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                        }
                        payload = {
                            "replyToken": reply_token,
                            "messages": [{
                                "type": "text",
                                "text": bot_response
                            }]
                        }
                        response = requests.post(reply_url, headers=headers, json=payload)

                        if response.status_code == 200:
                            logger.info(f"✅ フィードバック処理完了")
                        else:
                            logger.error(f"❌ 返信エラー: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ LINE API呼び出しエラー: {e}")

                    continue  # 次のイベントへ

                # 通常メッセージ処理（バッファリング対応）
                # 短時間の連続メッセージを結合して処理
                logger.info(f"📩 メッセージ受信: {user_message[:30]}...")

                # バッファに追加（特殊コマンドはFalseが返る）
                buffered = await message_buffer.add_message(
                    user_id=user_id,
                    message=user_message,
                    reply_token=reply_token,
                    callback=process_combined_message
                )

                if buffered:
                    # バッファリングされた場合は即座に200を返す
                    # process_combined_messageがバッファタイムアウト後に呼ばれる
                    logger.info(f"⏳ バッファリング中: {user_id[:8]}...")
                    continue  # 次のイベントへ

                # 特殊コマンドはバッファリングせず即座に処理
                # （ただし、ほとんどの特殊コマンドは上のセクションで処理済み）
                # ここに到達する場合は単一メッセージとして処理
                await process_combined_message(
                    user_id=user_id,
                    combined_message=user_message,
                    reply_token=reply_token,
                    message_count=1
                )

    return JSONResponse(content={"status": "ok"})


# ========================================
# メイン実行
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
