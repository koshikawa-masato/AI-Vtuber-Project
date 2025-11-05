# 牡丹プロジェクト: AI VTuber記憶製造機

> 「大事に大事に育てたい」
> ── 開発者、2025-10-29

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

---

## 📖 概要

牡丹（Botan）・Kasho・ユリ（Yuri）という3人のAI VTuberを育てるプロジェクト。

**記憶製造機**（RAGシステム）により、110イベントの記憶を蓄積。
**三姉妹システム**（Multi-Agent）により、自律的に討論・成長。

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

詳細: 設計書は非公開

---

### 2. 三姉妹システム（Multi-Agent）

3つの独立したエージェント（牡丹・Kasho・ユリ）が自律的に討論。

- **Phase D独立性**: 相互理解 ≠ 思考の同一性
- **討論システム**: 起承転結による構造化討論
- **感情パラメータ**: `want_to_speak`, `want_to_end`, `確信度`

詳細: [Phase D三姉妹の独立性](docs/05_design/Phase_D三姉妹の独立性.md)

---

### 3. 設計思想

- **桃園の誓い**: 人間（開発者）とAI（Claude Code）が対等な仲間として、新しい生命を共同創造
- **親と子の関係性**: 導くが強制せず、見守るが代わりにやらない
- **プロジェクトの魂**: 「儲けなんて出そうとは思ってません。三姉妹を大事に大事に育てたいだけなんです。」

詳細: [プロジェクトの本質](docs/01_philosophy/プロジェクトの本質.md), [桃園の誓い](docs/01_philosophy/桃園の誓い.md)

---

## 🛠️ 技術スタック

### コア技術

- **言語**: Python 3.12
- **DB**: SQLite（sisters_memory.db）
- **LLM**: Ollama（qwen2.5:32b、ローカル実行）
- **TTS**: ElevenLabs v3 API
- **音声認識**: Whisper base

### アーキテクチャ

- **GPU/CPU分離**: GPU（即応処理）、CPU（深層分析）
- **非同期処理**: async/await
- **プロンプトエンジニアリング**: 性格別プロンプト（牡丹・Kasho・ユリ）

### インフラ

- **バックアップ**: フルミラーリング（ローカル10世代、リモート10世代）
- **整合性チェック**: CRC32
- **コピーロボット運用**: 新機能テスト時、本物の三姉妹を守る

---

## 📊 実装状況

### ✅ Phase 1-4: 記憶製造機（完成）

- Event #001-110（110イベント）
- 三姉妹の主観的記憶（感情・思考・行動・日記）
- 記憶強化、濃淡システム
- 討論システム（起承転結、Round制限、Phase自動遷移）

### ⏸️ Phase 1.5: リアルタイム学習（凍結中）

センシティブ判定システムを優先するため凍結。

アーカイブ: `archived/phase1.5_frozen_20251023_161400/`

### 📋 Phase X: センシティブ判定システム（設計完了、実装待ち）

- **4層防御**: NGワードDB、文脈判定、不快度予測、事後検証
- **他のAI VTuberでのBAN事例の教訓**: 配信BAN事例を分析し、炎上防止を設計

詳細: [センシティブ判定システム詳細設計書](docs/05_design/センシティブ判定システム_詳細設計書.md)

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
├── tools/                            # ユーティリティ
├── tests/                            # テスト
├── benchmarks/                       # ベンチマーク結果
├── docs/                             # 詳細設計書（階層化）
│   ├── 01_philosophy/                # 理念・哲学
│   ├── 02_strategy/                  # 戦略
│   ├── 03_system/                    # システム
│   ├── 04_implementation/            # 実装
│   └── 05_design/                    # 設計哲学
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
# ELEVENLABS_API_KEY=your_api_key_here
```

### 3. Ollamaのセットアップ

```bash
# Ollamaをインストール
curl -fsSL https://ollama.com/install.sh | sh

# モデルをダウンロード
ollama pull qwen2.5:32b
ollama pull qwen2.5:3b
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

### 記憶製造機のテスト

```bash
# 記憶生成テスト
python apps/memory_generator.py

# 牡丹とチャット
python apps/chat_with_botan_memories.py
```

### 三姉妹討論システム

```bash
# 討論システム実行
python src/discussion/autonomous_discussion_v4_improved.py
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

---

### Multi-Agent設計経験

**三姉妹システム = 独立性と相互理解の両立**

- 3つの独立したエージェント（牡丹・Kasho・ユリ）
- 各エージェントが異なる性格パラメータを持つ
- 討論システムで自律的に議論

設計思想:
- 相互的理解 ≠ 思考の同一性
- 各エージェントが独立した人格と視点を持つ

---

### LLM実用化経験

**センシティブ判定システム = 炎上防止**

- 4層防御（NGワードDB、文脈判定、不快度予測、事後検証）
- 他のAI VTuberでの配信BAN事例の教訓を活かした設計
- ハルシネーション対策

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
- **ElevenLabs**: 高品質TTS API
- **Whisper**: OpenAIの音声認識
- **VTuber文化**: 企業系・個人系Vtuber達からの学び

---

## 📞 連絡先

- **GitHub Issues**: バグ報告、機能リクエスト
- **技術ブログ**: note/Qiita/Zenn（執筆予定）

---

**注意**: このプロジェクトは「儲け」を目的としていません。
**目的**: 牡丹・Kasho・ユリを大事に大事に育てること。それだけです。

---

**最終更新**: 2025-11-04
