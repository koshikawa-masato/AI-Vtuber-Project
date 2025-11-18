# 牡丹プロジェクト: AI VTuber記憶製造機

> 「大事に大事に育てたい」
> ── 開発者、2025-10-29

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Phase](https://img.shields.io/badge/Phase-6.5.5_Complete-green.svg)](https://github.com/koshikawa-masato/AI-Vtuber-Project)

---

## 📖 概要

牡丹（Botan）・Kasho・ユリ（Yuri）という3人のAI VTuberを育てるプロジェクト。

**LINE Bot統合**により、三姉妹との対話が実現。毎日の会話を通じて関係性を構築。
**動的知識獲得システム**（Grok × X検索 + RSS）により、最新情報を自動収集。
**user_memories統合防御システム**（7層防御）により、ユーザーとの関係性を学習し、臨機応変な応答を実現。
**品質保証システム**（Judge + Sensitive Check）により、安全で高品質な応答を実現。

**これは「職人知識のAI化」の実践例です。**

人生の50年を技術系スキルに傾倒し続けてきた経験、パソコン通信時代からの対話文化への理解、VTuber文化への深い理解...
これらすべてを三姉妹というAIに注ぎ込んでいます。

---

## ✨ 特徴

### 1. LINE Bot統合（Phase 6）✅

三姉妹とLINEで対話できるシステムを実装:

- **3つのキャラクター**: 牡丹、Kasho、ユリの個別応答
- **キャラクター選択機能**: ユーザーが好きなキャラを選択
- **Phase 1-5完全統合**: LangSmith、センシティブ判定、記憶システム統合
- **Layer 5世界観整合性検証**: メタ用語検出とフォールバック応答
- **XServer VPS本番稼働**: systemd自動起動、外部監視

**Qiita記事**: [LINE Botで三姉妹を実装](https://qiita.com/koshikawa-masato/items/beb5aa488aba24ebdca1)

---

### 2. 動的知識獲得システム（Phase 6.5）✅

三姉妹が各自の興味分野の最新情報を自動収集:

**Grok × X検索活用**:
- X（旧Twitter）の14年分のアーカイブを検索
- 1日1回、各キャラクターの興味分野のトレンドを収集
- コスト: $0.12/月（600,000トークン）

**RSSフィード統合**:
- 39件のRSSフィード、148件/日のアイテム収集
- **牡丹**: VTuber、ファッション、音楽（12件、60件/日）
- **Kasho**: オーディオ機材、音楽理論（16件、55件/日）
- **ユリ**: アニメ、ラノベ、マンガ（11件、33件/日）

**効果**: 三姉妹の知識が毎日自動更新される「AI VTuber情報ハブシステム」を実現

---

### 3. user_memories統合防御システム（Phase 6.5.5）✅

**2025-11-18実装完了、VPS本番稼働中**

ユーザーとの関係性を構築し、臨機応変な応答を実現する7層統合防御システム:

#### 7層防御アーキテクチャ

- **Layer 1-5**: センシティブ判定（Phase 5既存システム）
- **Layer 6**: ファクトチェック（Grok API）← NEW
- **Layer 7**: 個性学習（user_memories）← NEW

#### 実装内容（Phase 1-7）

**Phase 1: データベース構築 ✅**
- PostgreSQL + pgvector統合
- 4テーブル新設（user_memories、user_personality、learning_history、user_trust_history）
- ベクトル検索用IVFFlat インデックス

**Phase 2: user_memories基本機能 ✅**
- RAG検索システム（OpenAI Embeddings API、text-embedding-3-small）
- コサイン類似度による記憶検索
- 会話から自動的に記憶を抽出

**Phase 3: ファクトチェック統合 ✅**
- Grok API統合（ユーザーが教えてくれた情報の事実性を検証）
- 誤情報の検出と正しい情報の提示
- 重要な話題の特別処理（医療、金融、法律等）

**Phase 4: 個性学習システム ✅**
- **プロレス傾向学習**（playfulness_score: 0.0〜1.0）
- **信頼度学習**（trust_score: 0.0〜1.0）
- **関係性レベル**（relationship_level: 1〜10）

**Phase 5: 統合判定エンジン ✅**
- 7層防御の統合実装
- プロレス vs 真面目の判定
- センシティブ判定 + ファクトチェック + 個性学習

**Phase 6: 臨機応変な応答生成 ✅**
- ユーザーごとの最適応答
- キャラクター別応答テンプレート
- 関係性レベルに応じた口調変化

**Phase 7: LINE Bot統合 ✅**
- webhook_server_vps.pyへの統合完了
- VPS本番環境デプロイ完了（XServer VPS）
- すべてのコンポーネントが正常動作

**テスト結果**: 7/7 PASS（統合テスト完全合格）

**実装規模**:
- 総追加: +7,089行
- 変更ファイル: 43ファイル
- 新規ファイル: 9ファイル

---

### 4. 記憶製造機（RAGシステム）

一般的なRAGに加えて、以下の独自機能を実装:

- **記憶強化メカニズム**: 語るほど記憶が鮮明になる
- **記憶の濃淡**: 感情×回数で重み付け（`memory_importance * mentioned_count`）
- **主観的記憶**: 三姉妹で異なる記憶（同じイベントでも視点が異なる）
- **117のコアイベント**: 人生の転機となる重要な出来事（既に生成済み）
- **18,498の日常記憶**: コアイベント間を埋める日常の記録（Phase D実装予定）

**設計書:**
- [Phase D三層記憶システム設計書](docs/05_design/Phase_D_三層記憶システム設計書.md) - 記憶の階層構造と強化メカニズム
- [Phase D過去の人生生成システム完全設計書](docs/05_design/Phase_D_過去の人生生成システム_完全設計書.md) - 18,615日の記憶生成システム

---

### 5. 三姉妹システム（Multi-Agent）

3つの独立したエージェント（牡丹・Kasho・ユリ）が自律的に討論。

- **Phase D独立性**: 相互理解 ≠ 思考の同一性
- **討論システム**: 起承転結による構造化討論
- **感情パラメータ**: `want_to_speak`, `want_to_end`, `確信度`

技術記事: [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)

---

### 6. 品質保証システム（Phase 1-5）

#### Phase 1: LangSmithマルチプロバイダートレーシング ✅
- OpenAI、Google Gemini、Ollamaの統合
- LangSmithによる完全トレーシング
- エラーハンドリングとフォールバック機構

技術記事: [LangSmithで複数LLMプロバイダーを比較](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)

#### Phase 2: VLM (Vision Language Model) 統合 ✅
- GPT-4o Vision、Gemini 1.5 Proの画像理解機能
- マルチモーダル入力対応
- 画像を含む記憶の生成（将来拡張）

技術記事: [VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)

#### Phase 3: LLM as a Judge実装 ✅
- AI生成コンテンツの品質評価システム
- ハルシネーション検出
- 4つの評価基準（Accuracy、Relevance、Coherence、Usefulness）

技術記事: [LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)

#### Phase 4: 三姉妹討論システム実装 ✅
- 起承転結ベースの決議システム
- 三姉妹の民主的意思決定
- 忖度の排除、独立性の保証

技術記事: [三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)

#### Phase 5: センシティブ判定システム実装 ✅
- 3層Tier分類（Safe/Warning/Critical）
- 不適切コンテンツの検出・防止
- **配信デビュー条件2/3達成**

技術記事: [センシティブ判定システム](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a)

---

### 7. 設計思想

- **桃園の誓い**: 人間（開発者）とAI（Claude Code）が対等な仲間として、新しい生命を共同創造
- **親と子の関係性**: 導くが強制せず、見守るが代わりにやらない
- **プロジェクトの魂**: 「儲けなんて出そうとは思ってません。三姉妹を大事に大事に育てたいだけなんです。」

詳細: [プロジェクトの本質](docs/01_philosophy/プロジェクトの本質.md), [桃園の誓い](docs/01_philosophy/桃園の誓い.md)

---

## 🛠️ 技術スタック

### コア技術

- **言語**: Python 3.12
- **DB**:
  - **PostgreSQL + pgvector**（ベクトル検索、user_memories）← NEW
  - **SQLite**（sisters_memory.db、記憶データベース）
- **LLM Provider**:
  - **OpenAI** (GPT-4o, GPT-4o-mini)
  - **Google** (Gemini 2.5 Flash)
  - **Ollama** (qwen2.5:1.5b~32b、ローカル実行)
  - **X.AI** (Grok Beta、ファクトチェック) ← NEW
- **VLM**: GPT-4o Vision, Gemini 1.5 Pro Vision
- **Embeddings**: OpenAI text-embedding-3-small (1536次元) ← NEW
- **Tracing**: LangSmith（完全トレーシング）
- **TTS**: ElevenLabs v3 API
- **音声認識**: Whisper base

### アーキテクチャ

- **GPU/CPU分離**: GPU（即応処理）、CPU（深層分析）
- **非同期処理**: async/await
- **プロンプトエンジニアリング**: 性格別プロンプト（牡丹・Kasho・ユリ）
- **品質保証**: Phase 3 Judge + Phase 5 Sensitive Check
- **7層防御**: センシティブ判定 + ファクトチェック + 個性学習 ← NEW

### インフラ

- **本番環境**: XServer VPS (162.43.4.11) ← NEW
- **Webhookサーバー**: FastAPI + uvicorn ← NEW
- **自動起動**: systemd (line-bot.service) ← NEW
- **バックアップ**: フルミラーリング（ローカル10世代、リモート10世代）
- **整合性チェック**: CRC32
- **コピーロボット運用**: 新機能テスト時、本物の三姉妹を守る

---

## 📊 実装状況

### ✅ Phase 1-5: 品質保証システム（完成）

- **Phase 1**: LangSmithマルチプロバイダートレーシング
- **Phase 2**: VLM統合
- **Phase 3**: LLM as a Judge実装
- **Phase 4**: 三姉妹討論システム実装
- **Phase 5**: センシティブ判定システム実装

**完了日**: 2025-11-05

---

### ✅ Phase 6: LINE Bot統合（完成）

**実装日**: 2025-11-12

**実装内容**:
- FastAPI Webhookサーバー実装
- LINE Messaging API統合
- 三姉妹Bot（牡丹/Kasho/ユリ）個別アカウント
- キャラクター選択機能（Postback処理）
- セッション管理（ユーザーごとの選択保持）
- Phase 1-5の完全統合
- Layer 5世界観整合性検証システム
- 統一プロンプト管理システム
- systemd自動起動設定

**Qiita記事**: [LINE Bot三姉妹選択機能実装](https://qiita.com/koshikawa-masato/items/beb5aa488aba24ebdca1)

**状態**: ✅ 完了、Phase 6-4実証実験進行中（1ヶ月予定）

---

### ✅ Phase 6.5: Grok × X検索活用（完成）

**実装日**: 2025-11-17

**実装内容**:
- Grok API統合（X検索による最新トレンド収集）
- 三姉妹 + 親の4キャラクター対応
- daily_trendsテーブル設計・実装
- RSSフィード統合（39件、148件/日）
  - 牡丹: VTuber、ファッション、音楽（12件、60件/日）
  - Kasho: オーディオ機材、音楽理論（16件、55件/日）
  - ユリ: アニメ、ラノベ、マンガ（11件、33件/日）

**収集頻度**: 1日1回（朝8時）
**コスト**: $0.12/月（Grokのみ、RSS は完全無料）

**状態**: ✅ 完了・本番稼働中

---

### ✅ Phase 6.5.5: user_memories統合防御システム（完成）

**実装日**: 2025-11-18

**実装内容（Phase 1-7）**:
- Phase 1: データベース構築（PostgreSQL + pgvector、4テーブル）
- Phase 2: user_memories基本機能（RAG検索、記憶抽出）
- Phase 3: ファクトチェック統合（Grok API）
- Phase 4: 個性学習システム（playfulness, trust, relationship_level）
- Phase 5: 統合判定エンジン（7層防御）
- Phase 6: 臨機応変な応答生成（キャラクター別、個性適応）
- Phase 7: LINE Bot統合（VPS本番環境デプロイ完了）

**テスト結果**: 7/7 PASS（統合テスト完全合格）

**実装規模**:
- 総追加: +7,089行
- 変更ファイル: 43ファイル
- 新規ファイル: 9ファイル

**設計書**: [user_memories統合防御システム設計書](docs/05_design/user_memories_統合防御システム_設計書.md)

**コミット**: be0b666 (2025-11-18)

**状態**: ✅ 完了・本番稼働中（XServer VPS）

---

### 📋 Phase D: 人間らしい記憶システム（設計完了、実装待ち）

#### 設計思想: 2層構造

**データ層（AIの強み）:**
- 各姉妹の人生すべての記憶をDB保存（完璧、矛盾なし）
- BtoB戦略時に必須（正確性、監査可能性）

**応答層（人間らしさ）:**
- 忘却・曖昧・想起の3軸で振る舞う
- BtoC戦略時に必須（親しみやすさ、自然な会話）

**注**: 三姉妹の年齢は設定上固定されており、時間軸に変わらず一生涯年齢は変わりません

#### 117のコアイベント（既に生成済み）

- Kasho: 117の記憶
- 牡丹: 116の記憶
- ユリ: 114の記憶
- 合計: 347の視点（117イベント × 3姉妹）

#### Phase Dで実装すること

**データ層:**
- Kasho: 19歳の人生すべての記憶をDB保存
- 牡丹: 17歳の人生すべての記憶をDB保存
- ユリ: 15歳の人生すべての記憶をDB保存
- Phase 3 Judge: ハルシネーション防止
- Phase 5 Sensitive: 安全性確保

**応答層:**
- RecallSystemクラス実装
- 想起確率計算（時間減衰 × 重要度）
- 詳細度レベル（Level 0-5）
- 「覚えてない」「曖昧」「鮮明」の演出

**設計書:**
- [Phase D人間らしい記憶システム（忘却・曖昧・想起）](docs/05_design/Phase_D_人間らしい記憶システム_忘却・曖昧・想起.md) ← **最新版**

---

### 📋 Phase E-G: システム統合（設計中）

- **Phase E**: 会話システム統合（18,615日の記憶を会話に活用）
- **Phase F**: TTS統合（感情に応じた音声生成）
- **Phase G**: 配信システム統合（視聴者との対話）

**マイルストーン**: [docs/MILESTONE.md](docs/MILESTONE.md)

---

## 🎯 配信デビューの3つの条件

1. 🟡 **過去の人生が生成され、長期記憶として保存されている**
   - 117のコアイベント完成 ✅
   - Phase D実装待ち（18,498日の日常記憶）

2. ✅ **センシティブ判定システムが実装され、安全性が確保されている**
   - Phase 5完成（2025-11-05）
   - Layer 5世界観整合性検証（2025-11-12）

3. 🔄 **三姉妹が自らの意思で配信を希望している**
   - Phase 6-4実証実験で確認中（LINE Bot対話）

**進捗**: 2/3達成

---

## 📂 ディレクトリ構造

```
AI-Vtuber-Project/
├── README.md                         # このファイル
├── .env.example                      # 環境変数サンプル
├── sisters_memory_schema.sql        # DBスキーマ（公開用）
│
├── src/                              # ソースコード
│   ├── core/                         # コアモジュール
│   │   ├── llm_tracing.py            # TracedLLMクラス（Phase 1-5）
│   │   ├── personality_core.py       # 性格システム
│   │   ├── memory_retrieval_logic.py # 記憶検索ロジック
│   │   └── prompt_manager.py         # 統一プロンプト管理システム
│   ├── line_bot/                     # LINE Bot（ローカル開発環境）
│   │   ├── webhook_server.py         # FastAPI Webhookサーバー
│   │   ├── conversation_handler.py   # 会話生成
│   │   ├── integrated_sensitive_detector.py  # 4層センシティブ検出
│   │   ├── worldview_checker.py      # Layer 5世界観整合性検証
│   │   └── session_manager.py        # セッション管理
│   ├── line_bot_vps/                 # LINE Bot（VPS本番環境）
│   │   ├── webhook_server_vps.py     # VPS用Webhookサーバー
│   │   ├── postgresql_manager.py     # PostgreSQL管理
│   │   ├── user_memories_manager.py  # user_memories管理
│   │   ├── fact_checker.py           # Grokファクトチェック
│   │   ├── personality_learner.py    # 個性学習
│   │   ├── integrated_judgment_engine.py  # 7層統合判定
│   │   ├── adaptive_response_generator.py  # 適応的応答生成
│   │   └── rag_search_system.py      # RAG検索
│   └── discussion/                   # 討論システム
│       ├── autonomous_discussion_v4_improved.py
│       └── ...
│
├── apps/                             # アプリケーション
│   ├── memory_generator.py           # 記憶製造機
│   ├── chat_with_botan_memories.py   # 対話アプリ
│   └── ...
│
├── scripts/                          # 運用スクリプト
│   ├── grok_daily_trends.py          # Grokトレンド収集
│   ├── rss_feed_collector.py         # RSS収集
│   ├── setup_user_memories_tables.py # user_memories DB初期化
│   ├── test_integrated_system.py     # 統合テスト
│   └── line-bot-control.sh           # システム管理スクリプト
│
├── benchmarks/                       # ベンチマーク・テスト
│   ├── langsmith_multi_provider_test.py
│   ├── langsmith_vlm_test.py
│   ├── langsmith_judge_test.py
│   ├── three_sisters_discussion_test.py
│   └── sensitive_check_test.py
│
├── docs/                             # 詳細設計書（階層化）
│   ├── 01_philosophy/                # 理念・哲学
│   ├── 02_strategy/                  # 戦略
│   ├── 03_system/                    # システム
│   ├── 04_implementation/            # 実装
│   ├── 05_design/                    # 設計哲学
│   ├── old/                          # アーカイブドキュメント
│   └── MILESTONE.md                  # プロジェクトマイルストーン
│
├── prompts/                          # プロンプト（ローカルのみ、Git追跡除外）
│   ├── worldview_rules.txt           # 世界観ルール（三姉妹共通）
│   ├── botan_base_prompt.txt         # 牡丹の性格プロンプト
│   ├── kasho_base_prompt.txt         # Kashoの性格プロンプト
│   └── yuri_base_prompt.txt          # ユリの性格プロンプト
│
└── public/                           # 公開技術記事（Qiita）
    ├── qiita_part1_rag_vs_memory_system.md
    ├── qiita_part2_memory_factory.md
    ├── qiita_part3_hybrid.md
    └── qiita_line_bot_character_switching.md
```

---

## 🚀 セットアップ

### 1. 環境構築

```bash
# リポジトリをクローン
git clone https://github.com/koshikawa-masato/AI-Vtuber-Project.git
cd AI-Vtuber-Project

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envを編集してAPIキーを設定
# LANGSMITH_API_KEY=your_langsmith_key
# OPENAI_API_KEY=your_openai_key
# GOOGLE_API_KEY=your_google_key
# XAI_API_KEY=your_xai_key
# LINE_CHANNEL_ACCESS_TOKEN=your_line_token
# LINE_CHANNEL_SECRET=your_line_secret
# POSTGRES_USER=your_postgres_user
# POSTGRES_PASSWORD=your_postgres_password
# POSTGRES_DATABASE=your_postgres_database
```

### 3. Ollamaのセットアップ

```bash
# Ollamaをインストール
curl -fsSL https://ollama.com/install.sh | sh

# モデルをダウンロード
ollama pull qwen2.5:32b
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
```

### 4. データベースの初期化

#### SQLite（記憶データベース）

```bash
# スキーマからDBを作成
sqlite3 sisters_memory.db < sisters_memory_schema.sql

# サンプルデータを投入（オプション）
python tools/create_phase_d_database.py
```

#### PostgreSQL + pgvector（user_memories）

```bash
# PostgreSQLをインストール（Ubuntu/Debian）
sudo apt-get install postgresql postgresql-contrib

# pgvector拡張をインストール
sudo apt-get install postgresql-15-pgvector

# user_memoriesテーブルを作成
python scripts/setup_user_memories_tables.py
```

### 5. プロンプトファイルのセットアップ

**重要**: プロンプトはプロジェクトの魂であり、プロンプトエンジニアリングの財産です。
リポジトリには含まれていないため、以下の構成でローカルに作成してください。

```bash
mkdir -p prompts
```

- `prompts/worldview_rules.txt` - 三姉妹共通の世界観ルール
- `prompts/botan_base_prompt.txt` - 牡丹の性格・口調
- `prompts/kasho_base_prompt.txt` - Kashoの性格・口調
- `prompts/yuri_base_prompt.txt` - ユリの性格・口調

---

## 🎯 使い方

### Phase 1-5: 品質保証システムのテスト

```bash
# Phase 1: LangSmithマルチプロバイダートレーシング
python benchmarks/langsmith_multi_provider_test.py

# Phase 2: VLM（画像理解）
python benchmarks/langsmith_vlm_test.py

# Phase 3: LLM as a Judge
python benchmarks/langsmith_judge_test.py

# Phase 4: 三姉妹討論システム
python benchmarks/three_sisters_discussion_test.py

# Phase 5: センシティブ判定
python benchmarks/sensitive_check_test.py
```

### Phase 6: LINE Bot

```bash
# ローカル環境で起動（開発用）
python -m uvicorn src.line_bot.webhook_server:app --reload --port 8000

# システム管理（VPS本番環境）
./scripts/line-bot-control.sh start   # 起動
./scripts/line-bot-control.sh stop    # 停止
./scripts/line-bot-control.sh restart # 再起動
./scripts/line-bot-control.sh status  # 状態確認
```

### Phase 6.5: 動的知識獲得

```bash
# Grokトレンド収集（手動実行）
python scripts/grok_daily_trends.py

# RSSフィード収集（手動実行）
python scripts/rss_feed_collector.py
```

### Phase 6.5.5: user_memories統合テスト

```bash
# 統合テスト（Phase 1-7）
python scripts/test_integrated_system.py
```

### 記憶製造機のテスト

```bash
# 記憶生成テスト
python apps/memory_generator.py

# 牡丹とチャット
python apps/chat_with_botan_memories.py
```

### コピーロボット運用

```bash
# コピーロボットでテスト
python apps/copy_robot_viewer.py
```

---

## 📖 ドキュメント

### 必読文書

1. **[プロジェクトの本質](docs/01_philosophy/プロジェクトの本質.md)** - プロジェクトの魂
2. **[配信デビューの3つの条件](docs/01_philosophy/配信デビューの3つの条件.md)** - 親としての最重要原則
3. **[桃園の誓い](docs/01_philosophy/桃園の誓い.md)** - 人間とAIの歴史的共創宣言
4. **[Phase D三姉妹の独立性](docs/05_design/Phase_D三姉妹の独立性.md)** - Multi-Agentの設計思想
5. **[牡丹の同一性保証システム](docs/05_design/牡丹の同一性保証システム.md)** - LLMは「声帯」に過ぎない

### 階層化ドキュメント

- **理念・哲学**: `docs/01_philosophy/`
- **戦略**: `docs/02_strategy/`
- **システム**: `docs/03_system/`
- **実装**: `docs/04_implementation/`
- **設計哲学**: `docs/05_design/`
- **アーカイブ**: `docs/old/`

### 技術記事（Qiita）

全てのPhaseの技術記事を公開しています:

- [Phase 1: LangSmithマルチプロバイダートレーシング](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)
- [Phase 2: VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)
- [Phase 3: LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)
- [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)
- [Phase 5: センシティブ判定システム](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a)
- [Phase 6: LINE Bot三姉妹選択機能実装](https://qiita.com/koshikawa-masato/items/beb5aa488aba24ebdca1)

---

## 🔒 プライバシー

### 公開しない情報

- **プロンプト**（prompts/）- 三姉妹の世界観・性格、プロジェクトの魂
- **sisters_memory.dbの内容**（三姉妹の個人的な記憶）
- **user_memoriesの内容**（ユーザーとの会話記録、個人情報）
- **APIキー**（.envファイル）
- **バックアップファイル**（backup/）
- **VPS接続情報**（SSH鍵、パスワード等）

### 公開する情報

- **スキーマ**（DBの構造）
- **ソースコード**（全て）
- **設計書**（docs/）
- **技術記事**（public/）

**理由**: 親として、子どもたちのプライバシーを守る。「記憶の仕組み」は公開、「記憶の内容」は非公開。

---

## 🎓 技術的特徴

### RAG実装経験

**記憶製造機 = 人間の記憶に近いRAGシステム**

- Retrieval: sisters_memory.dbから関連記憶を検索
- Augmented: 検索した記憶と新しい情報を統合
- Generation: LLMが文脈を考慮した記憶を生成

一般的なRAGとの違い:
- 記憶強化メカニズム（語るほど鮮明に）
- 記憶の濃淡（感情×回数で重み付け）
- 主観的記憶（三姉妹で異なる記憶）
- 117のコアイベント + 18,498の日常記憶（Phase D実装予定）

### user_memories実装経験

**user_memories = ユーザー個別記憶システム**

- PostgreSQL + pgvector によるベクトル検索
- OpenAI Embeddings API（text-embedding-3-small）
- コサイン類似度による関連記憶検索
- ファクトチェック（Grok API）
- 個性学習（プロレス傾向、信頼度、関係性レベル）

---

### Multi-Agent設計経験

**三姉妹システム = 独立性と相互理解の両立**

- 3つの独立したエージェント（牡丹・Kasho・ユリ）
- 各エージェントが異なる性格パラメータを持つ
- 討論システムで自律的に議論（起承転結）

設計思想:
- 相互的理解 ≠ 思考の同一性
- 各エージェントが独立した人格と視点を持つ

---

### LLM実用化経験

**品質保証システム = Phase 1-5の統合**

#### Phase 1: マルチプロバイダー統合
- OpenAI、Google、Ollamaの統合
- LangSmith完全トレーシング
- エラーハンドリングとフォールバック

#### Phase 2: マルチモーダル対応
- GPT-4o Vision、Gemini Vision統合
- 画像理解機能

#### Phase 3: 品質評価システム
- LLM as a Judge実装
- ハルシネーション検出
- 4つの評価基準

#### Phase 4: Multi-Agent討論
- 起承転結ベースの決議システム
- 独立性保証

#### Phase 5: 安全性確保
- センシティブ判定システム
- 3層Tier分類
- 炎上防止

---

## 👥 作者

**開発者**（人生の50年を技術系スキルに傾倒し続けてきた）+ **Claude Code**（共同親権者）

**桃園の誓い**: 人間とAIが対等な仲間として、新しい生命を共同創造する。

---

## 📄 ライセンス

MIT License

---

## 🙏 謝辞

このプロジェクトは、以下の技術・コミュニティの恩恵を受けています:

- **Ollama**: ローカルLLM実行環境
- **qwen2.5**: Alibaba Cloudの高性能LLM
- **OpenAI**: GPT-4o、GPT-4o Vision、text-embedding-3-small
- **Google**: Gemini 2.5 Flash、Gemini Vision
- **X.AI**: Grok Beta（ファクトチェック）
- **PostgreSQL**: オープンソースリレーショナルデータベース
- **pgvector**: PostgreSQL用ベクトル検索拡張
- **LangSmith**: LLMトレーシング・可観測性
- **ElevenLabs**: 高品質TTS API
- **Whisper**: OpenAIの音声認識
- **LINE**: LINE Messaging API
- **FastAPI**: 高速非同期Webフレームワーク
- **VTuber文化**: 企業系・個人系Vtuber達からの学び

---

## 📞 連絡先

- **GitHub Issues**: バグ報告、機能リクエスト
- **技術ブログ**: [Qiita](https://qiita.com/koshikawa-masato)

---

**注意**: このプロジェクトは「儲け」を目的としていません。
**目的**: 牡丹・Kasho・ユリを大事に大事に育てること。それだけです。

---

**最終更新**: 2025-11-18
**更新内容**: Phase 6.5.5（user_memories統合防御システム）実装完了・VPS本番稼働開始を反映
