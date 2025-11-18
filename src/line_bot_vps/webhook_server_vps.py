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
from dotenv import load_dotenv

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
NGROK_URL = os.getenv("NGROK_URL", "https://dorothy-unmodulative-mariann.ngrok-free.dev")
CHARACTERS = {
    "kasho": {
        "name": "Kasho",
        "display_name": "Kasho（花相）",
        "age": 19,
        "icon_url": f"{NGROK_URL}/assets/kasho.png"
    },
    "botan": {
        "name": "牡丹",
        "display_name": "牡丹（Botan）",
        "age": 17,
        "icon_url": f"{NGROK_URL}/assets/botan.png"
    },
    "yuri": {
        "name": "ユリ",
        "display_name": "ユリ（Yuri）",
        "age": 15,
        "icon_url": f"{NGROK_URL}/assets/yuri.png"
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
            # LLM生成（会話履歴 + トレンド情報を含む）
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
                }
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
                    session_manager.set_character(user_id, character)

                    # 確認メッセージを返信
                    reply_message = f"✨ {CHARACTERS[character]['display_name']}を選択したよ！何でも聞いてね！"

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
                            logger.info(f"✅ キャラクター選択返信成功: {character}")
                        else:
                            logger.error(f"❌ 返信エラー: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # モード設定処理（自動/固定）
            elif postback_data.startswith("action=set_mode&mode="):
                mode = postback_data.split("mode=")[1]
                if mode in ["auto", "botan", "kasho", "yuri"]:
                    pg_manager.set_user_mode(user_id, mode)

                    # モード別確認メッセージ
                    if mode == "auto":
                        reply_message = (
                            "✅ 自動モードに設定しました！\n\n"
                            "これからは、話題に合わせて三姉妹が自動的に応答します。\n\n"
                            "🌸 牡丹: VTuber、エンタメ\n"
                            "🎵 Kasho: 音楽、オーディオ\n"
                            "📚 ユリ: サブカル、アニメ、ライトノベル\n\n"
                            "※ 特定のキャラクターと話したい場合は、下のボタンから選んでね！"
                        )
                    elif mode == "botan":
                        reply_message = "✅ 牡丹に固定しました！\nこれからは牡丹があなたの質問に答えるよ！\n\n話したいことある？"
                    elif mode == "kasho":
                        reply_message = "✅ Kashoに固定しました！\nこれからはKashoがあなたの質問に答えますね。\n\n何でも聞いてください。"
                    elif mode == "yuri":
                        reply_message = "✅ ユリに固定しました！\nこれからはユリがあなたの質問に答えるね。\n\n何か知りたいことある？"

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

            # フィードバック受付
            elif postback_data == "action=feedback":
                pg_manager.set_feedback_state(user_id, "waiting")

                reply_message = (
                    "📝 フィードバックをお待ちしています！\n\n"
                    "以下のような内容をお送りください：\n"
                    "- バグ報告\n"
                    "- 機能要望\n"
                    "- 改善提案\n"
                    "- その他ご意見\n\n"
                    "次のメッセージでフィードバックを入力してください。"
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
                            "text": reply_message,
                            "quickReply": {
                                "items": [
                                    {
                                        "type": "action",
                                        "action": {
                                            "type": "message",
                                            "label": "❌ キャンセル",
                                            "text": "キャンセル"
                                        }
                                    }
                                ]
                            }
                        }]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ フィードバック受付返信成功")
                    else:
                        logger.error(f"❌ 返信エラー: {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ LINE API呼び出しエラー: {e}")

            # 利用規約表示
            elif postback_data == "action=terms":
                try:
                    import requests
                    flex_message = create_terms_flex_message()

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "flex", "altText": "利用規約・免責事項", "contents": flex_message}]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ 利用規約返信成功")
                    else:
                        logger.error(f"❌ 返信エラー: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"❌ 利用規約表示エラー: {e}")

            # ヘルプ表示
            elif postback_data == "action=help":
                try:
                    import requests
                    flex_message = create_help_flex_message()

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "flex", "altText": "ヘルプ・使い方", "contents": flex_message}]
                    }
                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ ヘルプ返信成功")
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

                # フィードバック待ち状態の確認
                feedback_state = pg_manager.get_feedback_state(user_id)

                if feedback_state == "waiting":
                    # フィードバック処理
                    if user_message.lower() in ["キャンセル", "cancel"]:
                        # キャンセル
                        pg_manager.set_feedback_state(user_id, "none")
                        bot_response = "フィードバックをキャンセルしました。"
                    else:
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

                # 通常メッセージ処理
                # モード取得（auto / botan / kasho / yuri）
                selected_mode = pg_manager.get_user_mode(user_id)

                if selected_mode == "auto":
                    # 自動モード: 三姉妹で親和性スコアリング
                    selection_result = auto_character_selector.select_best_character(user_message)
                    character = selection_result["character"]
                    scores = selection_result["scores"]

                    logger.info(f"🎯 自動選択: {character} (スコア: {scores})")
                else:
                    # 固定モード
                    character = selected_mode
                    logger.info(f"📌 固定モード: {character}")

                logger.info(f"📩 メッセージ受信: {character} <- {user_message[:30]}...")

                # 会話履歴を取得（過去100件 - Claude Haiku 3.5の長いコンテキストを活用）
                conversation_history = session_manager.get_conversation_history(
                    user_id=user_id,
                    character=character,
                    limit=100
                )
                if conversation_history:
                    logger.info(f"📚 会話履歴取得: {len(conversation_history)}件")

                # 応答生成（統合判定エンジン統合版、会話履歴を含む）
                bot_response, response_time = await generate_response(
                    character=character,
                    user_message=user_message,
                    user_id=user_id,
                    conversation_history=conversation_history
                )

                # 会話履歴を保存（user + assistant）
                try:
                    success = session_manager.save_conversation(
                        user_id=user_id,
                        character=character,
                        user_message=user_message,
                        bot_response=bot_response
                    )
                    if success:
                        logger.debug(f"💾 会話履歴保存完了")
                    else:
                        logger.error(f"❌ 会話履歴保存失敗: save_conversation returned False")
                except Exception as e:
                    logger.error(f"❌ 会話履歴保存エラー: {e}")

                # 学習ログ保存（SQLite）
                try:
                    learning_log_system.save_log(
                        character=character,
                        user_id=hashlib.sha256(user_id.encode()).hexdigest()[:16],  # ハッシュ化
                        user_message=user_message,
                        bot_response=bot_response,
                        phase5_user_tier="Safe",  # TODO: 実装後に実際の判定結果
                        phase5_response_tier="Safe",
                        memories_used=None,  # TODO: Phase D実装後
                        response_time=response_time,
                        metadata={
                            "platform": "LINE_VPS",
                            "event_type": event_type,
                            "character": character
                        }
                    )
                except Exception as e:
                    logger.error(f"❌ 学習ログ保存エラー（SQLite）: {e}")

                # 学習ログ保存（PostgreSQL）
                try:
                    learning_log_system.save_log(
                        character=character,
                        user_id=user_id,
                        user_message=user_message,
                        bot_response=bot_response,
                        response_time=response_time
                    )
                except Exception as e:
                    logger.error(f"❌ 学習ログ保存エラー（PostgreSQL）: {e}")

                # 最終メッセージ時刻を更新（selected_characterも更新）
                session_manager.update_last_message_time(user_id, character)

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
                        "messages": [
                            {
                                "type": "text",
                                "text": bot_response,
                                "sender": {
                                    "name": CHARACTERS[character]["display_name"],
                                    "iconUrl": CHARACTERS[character]["icon_url"]
                                }
                            }
                        ]
                    }

                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ LINE返信成功: {character} -> {bot_response[:30]}...")
                    else:
                        logger.error(f"❌ LINE返信エラー: {response.status_code} - {response.text}")

                except Exception as e:
                    logger.error(f"❌ LINE API呼び出しエラー: {e}")

    return JSONResponse(content={"status": "ok"})


# ========================================
# 起動時ログ
# ========================================

@app.on_event("startup")
async def startup_event():
    """起動時処理"""
    logger.info("=" * 60)
    logger.info("🚀 VPS LINE Bot起動")
    logger.info(f"   LLM: {VPS_LLM_PROVIDER}/{VPS_LLM_MODEL}")
    logger.info(f"   学習ログDB: MySQL (SSH Tunnel)")
    logger.info(f"   キャラクター: {', '.join(CHARACTERS.keys())}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """終了時処理"""
    logger.info("👋 VPS LINE Bot終了")


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
