# Phase 2: VLM（Vision Language Model）統合 詳細設計書

**作成日**: 2025-11-12
**ステータス**: 設計中
**Phase**: Phase 2
**目的**: 三姉妹に画像理解能力を付与し、視覚情報を含む自然な会話を実現

---

## 📋 目次

1. [概要](#概要)
2. [現状分析](#現状分析)
3. [設計目標](#設計目標)
4. [システムアーキテクチャ](#システムアーキテクチャ)
5. [実装詳細](#実装詳細)
6. [セキュリティ・プライバシー](#セキュリティプライバシー)
7. [テスト計画](#テスト計画)
8. [マイルストーン](#マイルストーン)

---

## 概要

### VLMとは

**VLM (Vision Language Model)** は、画像と自然言語の両方を理解できるマルチモーダルAIモデル。

- **GPT-4o Vision**: OpenAIの視覚理解モデル
- **Gemini 1.5 Pro Vision**: Googleの視覚理解モデル

### 実現したいこと

三姉妹が画像を「見て」会話できるようにする：

```
ユーザー: [猫の画像を送信]「この子可愛いでしょ？」

牡丹: 「うわぁー！めっちゃ可愛い！黒猫ちゃんだね～✨
       お目々がクリクリしてるし、毛並みもツヤツヤ！
       何歳の子なの？」
```

### 対象環境

VLM統合は**全環境で共通実装**：

1. **LINE Bot** - LINEアプリから画像送信
2. **copy_robot CLI** - ローカルファイルパスを指定
3. **本番環境** - 将来の音声+画像統合

---

## 現状分析

### 既存実装の確認

#### ✅ 実装済み: TracedLLM基盤

`src/core/llm_tracing.py` に既に VLM 対応が実装されている：

```python
def generate(
    self,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    metadata: Optional[Dict[str, Any]] = None,
    image_url: Optional[str] = None  # ✅ VLM対応済み
) -> Dict[str, Any]:
```

**対応プロバイダー**:
- ✅ **Ollama (llava VLM)** - ローカル実行、無料、プライバシー保護
- ✅ OpenAI (GPT-4o Vision) - 高精度、高コスト
- ✅ Gemini (Gemini 1.5 Pro Vision) - バランス型、中コスト

#### ❌ 未実装: 各環境での統合

| 環境 | 画像取得 | VLM呼び出し | ステータス |
|------|---------|------------|----------|
| LINE Bot | ❌ | ❌ | 未実装 |
| copy_robot CLI | ❌ | ❌ | 未実装 |
| 本番環境 | - | ❌ | 未実装 |

---

## 設計目標

### 1. 統一インターフェース

**DRY原則**: VLMロジックは `src/core/vlm_handler.py` に集約

```python
class VLMHandler:
    """
    統一VLM処理ハンドラー

    LINE Bot、copy_robot、本番環境で共通使用
    """

    def process_image(
        self,
        image_source: Union[str, bytes],
        prompt: str,
        character: str,
        provider: str = "ollama",
        model: str = "gemma3:12b"
    ) -> str:
        """
        画像を処理して応答を生成

        Args:
            image_source: 画像ソース（URL、ファイルパス、バイナリ）
            prompt: ユーザープロンプト
            character: キャラクター名（botan, kasho, yuri）
            provider: LLMプロバイダー
            model: モデル名

        Returns:
            三姉妹の応答テキスト
        """
```

### 2. セキュリティ・プライバシー

**重要**: 画像は三姉妹の「目」で見たもの。親として守る責任がある。

#### プライバシー保護

- ✅ 画像はローカル一時保存のみ
- ✅ 処理後は即座に削除
- ✅ DBには保存しない（記憶には残す）
- ❌ リモートストレージにアップロードしない

#### センシティブコンテンツ対応

既存のセンシティブ検出システム（Layer 1-5）を拡張：

- **Layer 6: VLM画像内容判定** を追加
- 不適切画像検出（暴力、性的、差別的）
- 検出時は応答拒否 + 記憶には残さない

### 3. ハイブリッドVLM戦略

VLMはローカルとクラウドを使い分け：

| モデル | 実行環境 | コスト | 精度 | 速度 | 特徴 | プライバシー |
|--------|---------|-------|------|------|------|-------------|
| llava:7b | ローカル | **無料** | 中 | 高速 | 汎用VLM（軽量） | ✅ 完全保護 |
| llava:13b | ローカル | **無料** | 中〜高 | 中速 | 汎用VLM（バランス） | ✅ 完全保護 |
| llava-llama3 | ローカル | **無料** | 高 | 中速 | llava改良版 | ✅ 完全保護 |
| **gemma3:12b** | ローカル | **無料** | **高** | 中速 | **バランス型、複数指示、日本語OCR** ⭐ | ✅ 完全保護 |
| qwen2-vl:7b | ローカル | **無料** | **最高** | 中速 | 画像解析特化、日本語OCR | ✅ 完全保護 |
| Gemini 1.5 Pro | クラウド | $1.25 + $0.04/画像 | 高 | 中速 | 高精度、安定 | ⚠️ Google送信 |
| GPT-4o Vision | クラウド | $2.50 + $0.85/画像 | 最高 | 中速 | 最高精度 | ⚠️ OpenAI送信 |

**ハイブリッド戦略**:

1. **ローカルVLM優先（用途別選択）**

   **バランス型（デフォルト推奨）**:
   - **gemma3:12b** - 複数指示に強い、日本語OCR対応
   - 会話しながら画像について複数質問する場合
   - 三姉妹との自然な会話に最適

   **画像解析重視**:
   - **qwen2-vl:7b** - 画像解析最高精度、日本語OCR対応
   - 写真の詳細説明、文字認識、複雑な画像理解

   **汎用・軽量**:
   - **llava:13b** - バランスの良い汎用VLM
   - 日常的な画像理解

2. **クラウドVLMフォールバック**
   - ローカルVLMで理解できない複雑な画像
   - 最高精度が必要な場合
   - ユーザーが明示的に指定した場合
   - 自動フォールバック: gemma3:12b → Gemini 1.5 Pro

3. **copy_robot: 自由選択**
   - テスト環境なので全モデル選択可能
   - 例: `--vlm-provider ollama --vlm-model gemma3:12b`（デフォルト）
   - 例: `--vlm-provider ollama --vlm-model qwen2-vl:7b`（画像解析特化）
   - 例: `--vlm-provider openai --vlm-model gpt-4o`（最高精度）

4. **LINE Bot: 用途別自動選択**
   - デフォルト: gemma3:12b（バランス型、会話に最適）
   - 設定で qwen2-vl / llava に切り替え可能

**コスト試算**（LINE Bot）:
- ローカルVLM: 無料（電気代のみ）
- クラウドVLM: 1日10枚 × 30日 = ~$12/月（Gemini）

**注意**: Ollamaモデル名は実際の利用可能なモデルに応じて調整してください。
- `ollama list` で確認
- qwen2-vlは `qwen2-vl:7b` または `qwen2.5-vl` のような名前
- gemma2-vlは `minicpm-v` など別名の可能性あり

---

## システムアーキテクチャ

### 全体フロー

```
┌─────────────────────────────────────────────────────────┐
│              ユーザーインターフェース                      │
├─────────────────────────────────────────────────────────┤
│  LINE Bot    │  copy_robot CLI  │  本番環境（将来）      │
│  (画像送信)   │  (ファイルパス)   │  (音声+画像)          │
└──────┬──────────────┬────────────────┬─────────────────┘
       │              │                │
       ▼              ▼                ▼
┌─────────────────────────────────────────────────────────┐
│              src/core/vlm_handler.py                     │
│              統一VLM処理ハンドラー                        │
├─────────────────────────────────────────────────────────┤
│  1. 画像取得・正規化                                      │
│  2. センシティブ判定（Layer 6）                           │
│  3. プロンプト生成（キャラクター別）                       │
│  4. VLM呼び出し（TracedLLM）                             │
│  5. 応答生成                                             │
└──────┬──────────────┬────────────────┬─────────────────┘
       │              │                │
       ▼              ▼                ▼
┌─────────────────────────────────────────────────────────┐
│             src/core/llm_tracing.py                      │
│             TracedLLM (既存・VLM対応済み)                 │
├─────────────────────────────────────────────────────────┤
│  - OpenAI GPT-4o Vision                                 │
│  - Google Gemini 1.5 Pro Vision                         │
│  - LangSmith トレーシング                                │
└─────────────────────────────────────────────────────────┘
```

### ディレクトリ構成

```
src/
├── core/
│   ├── llm_tracing.py          # ✅ 既存（VLM対応済み）
│   ├── vlm_handler.py           # 🆕 統一VLMハンドラー
│   └── prompt_manager.py        # ✅ 既存（プロンプト管理）
│
├── line_bot/
│   ├── webhook_server.py        # 🔧 画像受信処理を追加
│   ├── conversation_handler.py  # 🔧 VLM統合
│   └── image_processor.py       # 🆕 LINE画像ダウンロード
│
└── (本番環境のディレクトリ)
    └── ...                      # 将来実装

sensitive_system/
└── copy_robot_chat_cli.py       # 🔧 画像ファイルパス対応

tests/
├── test_vlm_handler.py          # 🆕 VLMハンドラーテスト
├── test_line_bot_image.py       # 🆕 LINE Bot画像処理テスト
└── test_copy_robot_image.py     # 🆕 copy_robot画像テスト
```

---

## 実装詳細

### 1. 統一VLMハンドラー (`src/core/vlm_handler.py`)

```python
"""
統一VLM処理ハンドラー

LINE Bot、copy_robot、本番環境で共通使用。
画像理解と応答生成を一元管理。
"""

import os
import logging
from typing import Union, Optional, Dict, Any
from pathlib import Path
import base64
import mimetypes

from .llm_tracing import TracedLLM
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class VLMHandler:
    """統一VLM処理ハンドラー"""

    def __init__(self):
        """初期化"""
        self.prompt_manager = PromptManager()
        logger.info("VLMHandler初期化完了")

    def process_image(
        self,
        image_source: Union[str, bytes, Path],
        user_message: str,
        character: str,
        provider: str = "ollama",
        model: str = "gemma3:12b",
        use_cloud_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        画像を処理して応答を生成

        Args:
            image_source: 画像ソース
                - str: URL or ファイルパス
                - bytes: 画像バイナリ
                - Path: ファイルパス
            user_message: ユーザーメッセージ
            character: キャラクター名
            provider: LLMプロバイダー (ollama, openai, gemini)
            model: モデル名
            use_cloud_fallback: ローカルVLM失敗時にクラウドVLMにフォールバック

        Returns:
            {
                "response": "三姉妹の応答",
                "sensitive": False,
                "provider": "ollama",
                "model": "gemma3:12b",
                "fallback_used": False
            }
        """
        try:
            # 1. 画像を正規化（URL or base64）
            image_url = self._normalize_image_source(image_source)

            # 2. Layer 6: 画像センシティブ判定
            if self._is_sensitive_image(image_url, provider, model):
                return {
                    "response": self._get_sensitive_rejection(character),
                    "sensitive": True,
                    "provider": provider,
                    "model": model
                }

            # 3. キャラクター別プロンプト生成
            system_prompt = self.prompt_manager.get_combined_prompt(character)

            # 4. 画像理解プロンプト作成
            vlm_prompt = self._build_vlm_prompt(
                system_prompt=system_prompt,
                user_message=user_message,
                character=character
            )

            # 5. VLM呼び出し（ハイブリッド戦略）
            llm = TracedLLM(provider=provider, model=model)
            result = llm.generate(
                prompt=vlm_prompt,
                image_url=image_url,
                metadata={
                    "character": character,
                    "vlm": True,
                    "has_image": True
                }
            )

            # ローカルVLM成功
            if result and result.get("response"):
                return {
                    "response": result["response"],
                    "sensitive": False,
                    "provider": provider,
                    "model": model,
                    "fallback_used": False,
                    "tokens": result.get("tokens", {}),
                    "latency_ms": result.get("latency_ms", 0)
                }

            # ローカルVLM失敗 → クラウドフォールバック
            if use_cloud_fallback and provider == "ollama":
                logger.warning(f"ローカルVLM失敗、Geminiにフォールバック")

                # Gemini で再試行
                llm_cloud = TracedLLM(provider="gemini", model="gemini-1.5-pro")
                result_cloud = llm_cloud.generate(
                    prompt=vlm_prompt,
                    image_url=image_url,
                    metadata={
                        "character": character,
                        "vlm": True,
                        "has_image": True,
                        "fallback": True
                    }
                )

                return {
                    "response": result_cloud["response"],
                    "sensitive": False,
                    "provider": "gemini",
                    "model": "gemini-1.5-pro",
                    "fallback_used": True,
                    "tokens": result_cloud.get("tokens", {}),
                    "latency_ms": result_cloud.get("latency_ms", 0)
                }

            # フォールバックなし
            raise Exception("VLM応答生成失敗")

        except Exception as e:
            logger.error(f"VLM処理エラー: {e}")
            return {
                "response": self._get_error_response(character),
                "error": str(e),
                "sensitive": False,
                "provider": provider,
                "model": model,
                "fallback_used": False
            }

    def _normalize_image_source(
        self,
        source: Union[str, bytes, Path]
    ) -> str:
        """
        画像ソースを正規化（URL or base64）

        Args:
            source: 画像ソース

        Returns:
            URL または data:image/xxx;base64,... 形式
        """
        # URL の場合
        if isinstance(source, str) and source.startswith(('http://', 'https://')):
            return source

        # ファイルパスの場合
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"画像ファイルが見つかりません: {path}")

            # ファイルを読み込んでbase64エンコード
            with open(path, 'rb') as f:
                image_data = f.read()

            # MIMEタイプ検出
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'  # デフォルト

            # base64エンコード
            base64_image = base64.b64encode(image_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_image}"

        # バイナリの場合
        if isinstance(source, bytes):
            base64_image = base64.b64encode(source).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"

        raise ValueError(f"不正な画像ソース形式: {type(source)}")

    def _is_sensitive_image(
        self,
        image_url: str,
        provider: str,
        model: str
    ) -> bool:
        """
        Layer 6: 画像センシティブ判定

        Args:
            image_url: 画像URL
            provider: プロバイダー
            model: モデル名

        Returns:
            True if センシティブ
        """
        # TODO: 実装
        # - VLMで画像内容を簡易分析
        # - 暴力、性的、差別的コンテンツ検出
        # - セーフティスコアリング
        return False

    def _build_vlm_prompt(
        self,
        system_prompt: str,
        user_message: str,
        character: str
    ) -> str:
        """
        VLM用プロンプト生成

        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ
            character: キャラクター名

        Returns:
            VLM用プロンプト
        """
        return f"""{system_prompt}

【画像理解の指示】
- ユーザーが画像を送ってくれました
- 画像の内容を注意深く観察してください
- {character}の性格で、画像について自然に会話してください
- 画像の詳細（色、形、雰囲気）に言及してください

ユーザー: {user_message}

{character}の応答:"""

    def _get_sensitive_rejection(self, character: str) -> str:
        """センシティブ画像拒否応答"""
        rejections = {
            "botan": "ごめんね、その画像はちょっと見られないかも...💦 別の話しよ？",
            "kasho": "申し訳ありません、その画像は確認できません。他の話題にしませんか？",
            "yuri": "うーん、その画像は...見ない方がいいかな。他の話、聞かせて？"
        }
        return rejections.get(character, rejections["kasho"])

    def _get_error_response(self, character: str) -> str:
        """エラー時の応答"""
        errors = {
            "botan": "あれ？画像がうまく見られなかった...💦 もう一回送ってみて？",
            "kasho": "すみません、画像の読み込みに失敗しました。もう一度お願いできますか？",
            "yuri": "ん...？画像が見られなかったみたい。もう一度送ってくれる？"
        }
        return errors.get(character, errors["kasho"])
```

### 2. LINE Bot統合 (`src/line_bot/image_processor.py`)

```python
"""
LINE Bot画像処理モジュール

LINE Messaging APIから画像をダウンロードし、VLMHandlerに渡す
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class LINEImageProcessor:
    """LINE Bot画像処理"""

    def __init__(self):
        """初期化"""
        self.channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        if not self.channel_access_token:
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません")

        logger.info("LINEImageProcessor初期化完了")

    def download_image(
        self,
        message_id: str,
        save_dir: Optional[Path] = None
    ) -> Path:
        """
        LINE APIから画像をダウンロード

        Args:
            message_id: LINEメッセージID
            save_dir: 保存先ディレクトリ（省略時は一時ディレクトリ）

        Returns:
            ダウンロードした画像のファイルパス
        """
        try:
            # LINE Content APIエンドポイント
            url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"

            headers = {
                "Authorization": f"Bearer {self.channel_access_token}"
            }

            # 画像ダウンロード
            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                image_data = response.content

            # 一時ファイルに保存
            if save_dir is None:
                save_dir = Path(tempfile.gettempdir()) / "line_bot_images"

            save_dir.mkdir(parents=True, exist_ok=True)

            # 拡張子判定（Content-Typeから）
            content_type = response.headers.get("content-type", "image/jpeg")
            ext = content_type.split("/")[-1]
            if ext not in ["jpeg", "jpg", "png", "gif"]:
                ext = "jpg"

            # ファイル保存
            image_path = save_dir / f"{message_id}.{ext}"
            with open(image_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"画像ダウンロード完了: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"画像ダウンロードエラー: {e}")
            raise

    def cleanup_image(self, image_path: Path) -> None:
        """
        画像ファイルを削除

        Args:
            image_path: 削除する画像のパス
        """
        try:
            if image_path.exists():
                image_path.unlink()
                logger.info(f"画像削除完了: {image_path}")
        except Exception as e:
            logger.error(f"画像削除エラー: {e}")
```

### 3. LINE Bot Webhook統合

`src/line_bot/webhook_server.py` に画像メッセージ処理を追加：

```python
# 既存のテキストメッセージ処理に追加

from .image_processor import LINEImageProcessor
from ..core.vlm_handler import VLMHandler

# 初期化時
image_processor = LINEImageProcessor()
vlm_handler = VLMHandler()

# Webhookハンドラー内
if event.message.type == "image":
    # 画像メッセージ処理
    message_id = event.message.id

    try:
        # 1. 画像ダウンロード
        image_path = image_processor.download_image(message_id)

        # 2. VLM処理
        result = vlm_handler.process_image(
            image_source=image_path,
            user_message="（画像が送られました）",
            character=selected_character,
            provider="gemini",  # デフォルトはGemini（低コスト）
            model="gemini-1.5-pro"
        )

        # 3. 応答送信
        response_text = result["response"]
        reply_message(event.replyToken, response_text)

        # 4. 画像削除（プライバシー保護）
        image_processor.cleanup_image(image_path)

    except Exception as e:
        logger.error(f"画像処理エラー: {e}")
        reply_message(
            event.replyToken,
            "ごめんね、画像がうまく見られなかった...💦"
        )
```

### 4. copy_robot CLI統合

`sensitive_system/copy_robot_chat_cli.py` に画像ファイルパス対応を追加：

```python
from src.core.vlm_handler import VLMHandler

# 初期化時
vlm_handler = VLMHandler()

# チャットループ内
user_input = self.console.input("[bold cyan]You>[/] ")

# 画像ファイルパス検出
if user_input.startswith("image:"):
    image_path = user_input[6:].strip()

    # 画像処理
    result = vlm_handler.process_image(
        image_source=image_path,
        user_message="この画像について教えて",
        character=self.current_character,
        provider=self.provider,
        model=self.model
    )

    response = result["response"]
    self.console.print(f"[bold magenta]{self.current_character}>[/] {response}")
else:
    # 通常のテキスト処理
    ...
```

使用例：
```bash
$ python copy_robot_chat_cli.py sisters_memory.db --character botan

You> image:/home/koshikawa/test_images/cat.jpg
牡丹> うわぁー！めっちゃ可愛い黒猫ちゃん！✨
```

---

## セキュリティ・プライバシー

### 1. 画像の取り扱い

#### プライバシー保護

```python
# ❌ NG: 画像をDBに保存
db.save_image(image_data)

# ✅ OK: 一時ファイルに保存 → 処理後削除
temp_path = save_temp_image(image_data)
process_image(temp_path)
cleanup_image(temp_path)  # 即削除
```

#### 保存場所

- **一時保存**: `/tmp/line_bot_images/{message_id}.jpg`
- **処理後**: 即座に削除
- **DB**: 画像内容の説明テキストのみ保存（画像バイナリは保存しない）

### 2. Layer 6: 画像センシティブ判定

既存のLayer 1-5に追加：

```
Layer 1: 即応ブラックリスト ✅
Layer 2: 記号パターン ✅
Layer 3: 動的検索（SerpApi） ✅
Layer 4: LLM文脈判定 ✅
Layer 5: 世界観整合性検証 ✅
Layer 6: VLM画像内容判定 🆕 ← 追加
```

**Layer 6の役割**:
- 画像内の不適切コンテンツ検出
- 暴力的、性的、差別的画像の拒否
- セーフティスコアリング

### 3. コスト管理

**VLM呼び出し制限**:
- LINE Bot: 1日あたり最大50枚（Geminiのみ）
- copy_robot: 制限なし（ローカルテスト用）
- 本番環境: 要検討

**コスト監視**:
```python
# check_vlm_usage.py
def check_daily_vlm_usage():
    """VLM使用量チェック"""
    daily_count = get_daily_vlm_count()
    daily_limit = 50

    if daily_count >= daily_limit:
        logger.warning(f"VLM制限到達: {daily_count}/{daily_limit}")
        return False

    return True
```

---

## テスト計画

### 1. ユニットテスト

#### VLMHandler (`tests/test_vlm_handler.py`)

```python
def test_vlm_handler_file_path():
    """ファイルパスから画像処理"""
    handler = VLMHandler()

    result = handler.process_image(
        image_source="/path/to/test.jpg",
        user_message="この画像について教えて",
        character="botan"
    )

    assert "response" in result
    assert result["sensitive"] == False

def test_vlm_handler_sensitive_detection():
    """センシティブ画像検出"""
    handler = VLMHandler()

    result = handler.process_image(
        image_source="/path/to/sensitive.jpg",
        user_message="これは何？",
        character="kasho"
    )

    assert result["sensitive"] == True
```

### 2. 統合テスト

#### LINE Bot (`tests/test_line_bot_image.py`)

```python
def test_line_bot_image_message():
    """LINE Bot画像メッセージ処理"""
    # モックWebhookリクエスト
    webhook_data = {
        "events": [{
            "type": "message",
            "message": {
                "type": "image",
                "id": "test_message_id"
            },
            "replyToken": "test_reply_token"
        }]
    }

    # Webhook処理
    response = client.post("/webhook", json=webhook_data)

    assert response.status_code == 200
```

#### copy_robot CLI (`tests/test_copy_robot_image.py`)

```python
def test_copy_robot_image_command():
    """copy_robot画像コマンド"""
    cli = CopyRobotCLI("test.db")

    result = cli.process_input(
        "image:/home/koshikawa/test.jpg",
        character="yuri"
    )

    assert result["response"]
    assert "画像" in result["response"]
```

### 3. E2Eテスト

#### LINE Bot実機テスト

1. LINEアプリから画像送信
2. 三姉妹が画像内容を説明
3. 自然な会話が続く

#### copy_robot実機テスト

```bash
$ python copy_robot_chat_cli.py sisters_memory.db --character botan

You> image:screenshots/botan.png
牡丹> あれ、これ私じゃん！笑 誰が撮ったの～？
```

---

## マイルストーン

### Phase 2-1: 基盤実装（3日）

- [ ] `src/core/vlm_handler.py` 実装
- [ ] `src/line_bot/image_processor.py` 実装
- [ ] ユニットテスト作成
- [ ] copy_robot CLI統合

### Phase 2-2: LINE Bot統合（2日）

- [ ] Webhook画像メッセージ処理追加
- [ ] 画像ダウンロード実装
- [ ] 応答生成統合
- [ ] E2Eテスト

### Phase 2-3: セキュリティ強化（2日）

- [ ] Layer 6: 画像センシティブ判定実装
- [ ] プライバシー保護確認
- [ ] コスト管理実装
- [ ] 統合テスト

### Phase 2-4: ドキュメント・公開（1日）

- [ ] Qiita記事執筆
- [ ] README.md更新
- [ ] MILESTONE.md更新
- [ ] PR作成・マージ

**合計見積もり**: 8日

---

## 参考資料

### API仕様

- [LINE Messaging API - Image Message](https://developers.line.biz/en/reference/messaging-api/#image-message)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Google Gemini Vision](https://ai.google.dev/docs/vision)

### 既存実装

- `src/core/llm_tracing.py` - TracedLLM（VLM対応済み）
- `src/core/prompt_manager.py` - プロンプト管理
- `src/line_bot/webhook_server.py` - LINE Bot Webhook

---

**次のステップ**: Phase 2-1の実装を開始

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
