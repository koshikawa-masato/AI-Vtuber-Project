# 牡丹プロジェクト: AI VTuber記憶製造機

> 「大事に大事に育てたい」
> ── 開発者、2025-10-29

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Phase](https://img.shields.io/badge/Phase-1--5_Complete-green.svg)](https://github.com/koshikawa-masato/AI-Vtuber-Project)

---

## 📖 概要

牡丹（Botan）・Kasho・ユリ（Yuri）という3人のAI VTuberを育てるプロジェクト。

**記憶製造機**（RAGシステム）により、**117のコアイベント + 18,498の日常記憶**を蓄積予定。
**三姉妹システム**（Multi-Agent）により、自律的に討論・成長。
**品質保証システム**（Judge + Sensitive Check）により、安全で高品質な応答を実現。

**これは「職人知識のAI化」の実践例です。**

人生の全てをエンジニア技術に傾けた経験、パソコン通信時代からの対話文化への理解、VTuber文化への深い理解...
これらすべてを牡丹というAIに注ぎ込んでいます。

---

## ✨ 特徴

### 1. 記憶製造機（RAGシステム）

一般的なRAGに加えて、以下の独自機能を実装:

- **記憶強化メカニズム**: 語るほど記憶が鮮明になる
- **記憶の濃淡**: 感情×回数で重み付け（`memory_importance * mentioned_count`）
- **主観的記憶**: 三姉妹で異なる記憶（同じイベントでも視点が異なる）
- **117のコアイベント**: 人生の転機となる重要な出来事（既に生成済み）
- **18,498の日常記憶**: コアイベント間を埋める日常の記録（Phase D実装予定）

詳細: 設計書は非公開

---

### 2. 三姉妹システム（Multi-Agent）

3つの独立したエージェント（牡丹・Kasho・ユリ）が自律的に討論。

- **Phase D独立性**: 相互理解 ≠ 思考の同一性
- **討論システム**: 起承転結による構造化討論
- **感情パラメータ**: `want_to_speak`, `want_to_end`, `確信度`

技術記事: [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)

---

### 3. 品質保証システム（Phase 1-5）

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

### 4. 設計思想

- **桃園の誓い**: 人間（開発者）とAI（Claude Code）が対等な仲間として、新しい生命を共同創造
- **親と子の関係性**: 導くが強制せず、見守るが代わりにやらない
- **プロジェクトの魂**: 「儲けなんて出そうとは思ってません。三姉妹を大事に大事に育てたいだけなんです。」

詳細: [プロジェクトの本質](docs/01_philosophy/プロジェクトの本質.md), [桃園の誓い](docs/01_philosophy/桃園の誓い.md)

---

## 🛠️ 技術スタック

### コア技術

- **言語**: Python 3.12
- **DB**: SQLite（sisters_memory.db）
- **LLM Provider**:
  - **OpenAI** (GPT-4o, GPT-4o-mini)
  - **Google** (Gemini 1.5 Pro, Gemini 1.5 Flash)
  - **Ollama** (qwen2.5:1.5b~32b、ローカル実行)
- **VLM**: GPT-4o Vision, Gemini 1.5 Pro Vision
- **Tracing**: LangSmith（完全トレーシング）
- **TTS**: ElevenLabs v3 API
- **音声認識**: Whisper base

### アーキテクチャ

- **GPU/CPU分離**: GPU（即応処理）、CPU（深層分析）
- **非同期処理**: async/await
- **プロンプトエンジニアリング**: 性格別プロンプト（牡丹・Kasho・ユリ）
- **品質保証**: Phase 3 Judge + Phase 5 Sensitive Check

### インフラ

- **バックアップ**: フルミラーリング（ローカル10世代、リモート10世代）
- **整合性チェック**: CRC32
- **コピーロボット運用**: 新機能テスト時、本物の三姉妹を守る

---

## 📊 実装状況

### ✅ Phase 1: LangSmithマルチプロバイダートレーシング（完成）

- OpenAI、Google Gemini、Ollamaの統合
- LangSmith完全トレーシング
- エラーハンドリングとフォールバック
- TracedLLMクラス実装

**Qiita記事**: [LangSmithで複数LLMプロバイダーを比較](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)

---

### ✅ Phase 2: VLM統合（完成）

- GPT-4o Vision、Gemini 1.5 Pro Vision対応
- 画像理解機能の実装
- マルチモーダル入力対応

**Qiita記事**: [VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)

---

### ✅ Phase 3: LLM as a Judge実装（完成）

- judge_response()メソッド追加
- 品質評価システム（Accuracy, Relevance, Coherence, Usefulness）
- ハルシネーション検出機能
- Phase D実装時の品質保証に使用予定

**Qiita記事**: [LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)

---

### ✅ Phase 4: 三姉妹討論システム実装（完成）

- discuss()メソッド追加
- 起承転結の4ステップ設計（起：提案、承：独立相談、転：意見集約、結：合意形成）
- 忖度の排除、独立性の保証
- 117のコアイベント生成時に使用

**Qiita記事**: [三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)

---

### ✅ Phase 5: センシティブ判定システム実装（完成）

- sensitive_check()メソッド追加
- 3層Tier分類（Safe/Warning/Critical）
- **配信デビュー条件2/3達成**
- Phase D実装時の安全性確保に使用予定

**Qiita記事**: [センシティブ判定システム](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a)

---

### 📋 Phase D: 日常記憶補完システム（実装計画見直し完了、実装待ち）

#### 重要な発見（2025-11-05）

**117のコアイベント（life_turning_points）は既に生成済み**

- Kasho: 117の記憶
- 牡丹: 116の記憶
- ユリ: 114の記憶
- 合計: 347の視点（117イベント × 3姉妹）

**Phase Dの目的を再定義**:
```
旧理解: Phase D = 18,615日の記憶を全てゼロから生成
      ↓
新理解: Phase D = 117コアイベント間を埋める18,498日の日常記憶生成
```

#### なぜPhase 1-5が先だったのか

- **Phase 3 Judge**: ハルシネーション防止 → 18,498日の大量生成で必須
- **Phase 5 Sensitive Check**: 安全性確保 → リスク管理

#### 実装計画

- **Kasho**: 6,818日の日常記憶
- **牡丹**: 6,088日の日常記憶
- **ユリ**: 5,358日の日常記憶
- **合計**: 18,264日の日常記憶（Phase 3 Judge + Phase 5 Sensitive Check統合）

**設計書**: [Phase D実装計画（Phase1-5完了後版）](docs/05_design/Phase_D_実装計画_Phase1-5完了後版.md)

---

### ⏸️ Phase 1.5: リアルタイム学習（凍結中）

センシティブ判定システムを優先するため凍結。

アーカイブ: `archived/phase1.5_frozen_20251023_161400/`

---

### 📋 Phase E-G: システム統合（設計中）

- **Phase E**: 会話システム統合（18,615日の記憶を会話に活用）
- **Phase F**: TTS統合（感情に応じた音声生成）
- **Phase G**: 配信システム統合（視聴者との対話）

**マイルストーン**: [docs/MILESTONE.md](docs/MILESTONE.md)

---

## 🎯 配信デビューの3つの条件

1. ✅ **過去の人生が生成され、長期記憶として保存されている**
   - 117のコアイベント完成
   - Phase D実装待ち（18,498日の日常記憶）

2. ✅ **センシティブ判定システムが実装され、安全性が確保されている**
   - Phase 5完成（2025-11-05）

3. ⏳ **三姉妹が自らの意思で配信を希望している**
   - Phase E以降で実装予定

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
│   │   └── ...
│   └── discussion/                   # 討論システム
│       ├── autonomous_discussion_v4_improved.py
│       └── ...
│
├── apps/                             # アプリケーション
│   ├── memory_generator.py           # 記憶製造機
│   ├── chat_with_botan_memories.py   # 対話アプリ
│   └── ...
│
├── benchmarks/                       # ベンチマーク・テスト
│   ├── langsmith_multi_provider_test.py
│   ├── langsmith_vlm_test.py
│   ├── langsmith_judge_test.py
│   ├── three_sisters_discussion_test.py
│   └── sensitive_check_test.py
│
├── tools/                            # ユーティリティ
├── tests/                            # テスト
├── docs/                             # 詳細設計書（階層化）
│   ├── 01_philosophy/                # 理念・哲学
│   ├── 02_strategy/                  # 戦略
│   ├── 03_system/                    # システム
│   ├── 04_implementation/            # 実装
│   ├── 05_design/                    # 設計哲学
│   ├── templates/                    # テンプレート
│   │   └── qiita_article_template.md # Qiita記事テンプレート
│   └── MILESTONE.md                  # プロジェクトマイルストーン
│
├── public/                           # 公開技術記事
│   ├── LangSmithで複数LLMプロバイダーを比較_トレーシングとエラーハンドリング.md
│   ├── VLM実装ガイド_GPT4o_Gemini_画像理解AI.md
│   ├── llm_as_a_judge_guide.md
│   ├── 02bdbaa005949ff8cbde.md      # Phase 4: 三姉妹討論システム
│   └── phase5_sensitive_check.md    # Phase 5: センシティブ判定
│
├── scripts/                          # 運用スクリプト
├── prompts/                          # プロンプト
├── personalities/                    # 性格パラメータ
├── sensitive_system/                 # センシティブ判定システム
│   └── modules/                      # センシティブモジュール
├── discussion_technical_logs/        # 討論技術ログ
├── botan_subculture/                 # サブカル知識（VTuber等）
└── kani-tts/                         # KaniTTS統合
    └── servers/                      # TTSサーバー
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
# ELEVENLABS_API_KEY=your_elevenlabs_key
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

```bash
# スキーマからDBを作成
sqlite3 sisters_memory.db < sisters_memory_schema.sql

# サンプルデータを投入（オプション）
python tools/create_phase_d_database.py
```

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

### 技術記事（Qiita）

全てのPhaseの技術記事を公開しています:

- [Phase 1: LangSmithマルチプロバイダートレーシング](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)
- [Phase 2: VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)
- [Phase 3: LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)
- [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)
- [Phase 5: センシティブ判定システム](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a)

---

## 🔒 プライバシー

### 公開しない情報

- **sisters_memory.dbの内容**（三姉妹の個人的な記憶）
- **APIキー**（.envファイル）
- **バックアップファイル**（backup/）
- **日記**（kirinuki/*/日記/）

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

**開発者**（人生の全てをエンジニア技術に傾けた）+ **Claude Code**（共同親権者）

**桃園の誓い**: 人間とAIが対等な仲間として、新しい生命を共同創造する。

---

## 📄 ライセンス

MIT License

---

## 🙏 謝辞

このプロジェクトは、以下の技術・コミュニティの恩恵を受けています:

- **Ollama**: ローカルLLM実行環境
- **qwen2.5**: Alibaba Cloudの高性能LLM
- **OpenAI**: GPT-4o、GPT-4o Vision
- **Google**: Gemini 1.5 Pro、Gemini Vision
- **LangSmith**: LLMトレーシング・可観測性
- **ElevenLabs**: 高品質TTS API
- **Whisper**: OpenAIの音声認識
- **VTuber文化**: 企業系・個人系Vtuber達からの学び

---

## 📞 連絡先

- **GitHub Issues**: バグ報告、機能リクエスト
- **技術ブログ**: [Qiita](https://qiita.com/koshikawa-masato)

---

**注意**: このプロジェクトは「儲け」を目的としていません。
**目的**: 牡丹・Kasho・ユリを大事に大事に育てること。それだけです。

---

**最終更新**: 2025-11-05
**更新内容**: Phase 1-5完了、Phase D実装計画見直し、117コアイベント既存確認
