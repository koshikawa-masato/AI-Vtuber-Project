# Copy Robot Interactive Chat Guide

**作成日**: 2025-10-27
**目的**: コピーロボットDBを使って三姉妹と会話し、記憶と学習語彙を確認

---

## システム概要

Copy Robot Interactive Chatは、コピーロボットのDB（`COPY_ROBOT_YYYYMMDD_HHMMSS.db`）を使って三姉妹と対話するシステムです。

### 主な機能

1. **インタラクティブ会話**
   - 三姉妹（牡丹・Kasho・ユリ）と自由に会話
   - 語彙統合システムにより、学習した単語を使った会話
   - センシティブ判定統合でNG発言を検出

2. **記憶の確認**
   - 最近のイベント表示
   - 各キャラクターの最近の記憶表示
   - 記憶検索（キーワード）

3. **学習語彙の確認**
   - 各キャラクターが学習した単語のリスト表示
   - 語彙の意味・語源・使用例の確認

4. **センシティブ判定**
   - ユーザーメッセージのNGワード検出
   - 定型応答による安全な会話

---

## 使い方

### 1. モデルのダウンロード（初回のみ）

一括ダウンロードスクリプトで、コピーロボットテスト用の全モデルをダウンロード：

```bash
cd /home/koshikawa/toExecUnit/sensitive_system
./download_all_models.sh
```

**ダウンロード内容（全Phase自動実行）**:
- **Phase 1**: 軽量モデル (<4GB) - qwen2.5:3b, llama3.2:1b, gemma2:2b等
- **Phase 2**: 中量モデル (6-10GB) - qwen2.5:7b, elyza:jp8b, mistral:7b等
- **Phase 3**: 重量モデル (16GB+) - qwen2.5:32b, 72b, llama3.1:70b等
- **Phase 4**: 超重量モデル (32GB+) - llama3.1:405b, phi3:large

**所要時間**: 10GbE環境で約2-4時間
**必要容量**: 約1TB
**ログ**: `/home/koshikawa/toExecUnit/logs/model_download_YYYYMMDD_HHMMSS.log`

---

### 2. 基本コマンド

```bash
cd /home/koshikawa/toExecUnit/sensitive_system
python3 copy_robot_chat_cli.py [Copy Robot DBパス] [オプション]
```

### オプション

- `--model <model_name>`: Ollamaモデル名（指定なしの場合、起動時にインタラクティブ選択）
- `--ollama-host <URL>`: OllamaホストURL（デフォルト: http://localhost:11434）

---

### 3. 実行方法

#### 3-1. インタラクティブモデル選択（推奨）

オプション無しで起動すると、モデル選択UIが表示されます：

```bash
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db
```

**表示内容**:
```
========================================
  Ollama Model Selection
========================================

Installed Models:
┏━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━┓
┃  # ┃ Model Name       ┃ Size ┃ Modified    ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━┩
│  1 │ qwen2.5:3b       │ 1.9  │ 2 hours ago │
│  2 │ qwen2.5:14b      │ 9.0  │ 5 weeks ago │
│  3 │ elyza:jp8b       │ 4.9  │ 3 weeks ago │
│  4 │ gemma2:2b        │ 1.6  │ 5 weeks ago │
└────┴──────────────────┴──────┴─────────────┘

Recommended for chat:
  • qwen2.5:3b (lightweight, fast)
  • qwen2.5:7b (balanced)
  • qwen2.5:14b (high quality)
  • elyza:jp8b (Japanese specialized)
  • microai/suzume-llama3 (Japanese chat)

Select model number [1]:
```

番号を入力してモデルを選択します。

---

#### 3-2. モデル指定起動

特定のモデルを指定して起動：

```bash
# 軽量モデル
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --model qwen2.5:3b

# 日本語特化モデル
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --model elyza:jp8b

# バランス型
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --model qwen2.5:14b

# Ollamaホスト指定
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --ollama-host http://192.168.1.100:11434
```

---

## 対話コマンド

### 1. 通常会話（三姉妹全員が応答）

```
あなた: こんにちは！

牡丹: こんにちは！何かお手伝いできることある？
Kasho: こんにちは。今日はどんなことを話しましょうか。
ユリ: こんにちは...今日はどんな日でしたか？
```

### 2. 特定のキャラクターと会話

```
あなた: @botan 配信って楽しい？

牡丹: 配信は楽しいよ！視聴者さんとコメントでやり取りできるのが好き。
```

**フォーマット**: `@<character> <message>`

**キャラクター名**:
- `botan`: 牡丹
- `kasho`: Kasho
- `yuri`: ユリ

### 3. キャラクター情報表示

```
あなた: info botan

═══ 牡丹 の情報 ═══

学習語彙数: 7語

┌────────────┬──────────────────────────────────────┐
│ 単語       │ 意味                                 │
├────────────┼──────────────────────────────────────┤
│ 配信       │ インターネットを通じて動画や音楽を...│
│ ありがとう │ 感謝を表す日本語の言葉。相手がして...│
│ stream     │ ライブ配信、ストリーミング。VTuber...│
│ ...        │ ...                                  │
└────────────┴──────────────────────────────────────┘

最近の記憶: 5件

2025-01-15
  今日はKashoと一緒に音楽を聴いた。ボカロの曲がめっちゃ良かった...

...
```

**フォーマット**: `info <character>`

### 4. 最近のイベント表示

```
あなた: events

                  最近のイベント（10件）
┌────┬─────────────────────────────────┬────────────┐
│ #  │ イベント名                      │ 日付       │
├────┼─────────────────────────────────┼────────────┤
│ 117│ 三姉妹のAI VTuber活動始動       │ 2025-01-05 │
│ 116│ 牡丹、Kasho、ユリでProject Botan│ 2024-12-25 │
│ ...│ ...                             │ ...        │
└────┴─────────────────────────────────┴────────────┘
```

**フォーマット**: `events`

### 5. 終了

```
あなた: exit
または
あなた: quit
```

---

## 語彙統合システム

### システムプロンプトへの統合

各キャラクターと会話する際、以下の情報がシステムプロンプトに自動的に統合されます：

**重要**: Copy Robot Chat CLIは、本番環境（`chat_with_*_memories.py`）と**完全に同じプロンプト**を使用します。これにより、コピーロボットの動作が本番環境と一致し、正確なテストが可能になります。

1. **基本性格プロンプト**（本番環境と同一）
   - 牡丹: 17歳の女子高生ギャル、LA育ちの帰国子女、ギャル語使用
   - Kasho: 19歳の大学生・長女、責任感が強く論理的、丁寧な口調
   - ユリ: 15歳の中学生・末っ子、洞察力が高く繊細、静かで思慮深い

2. **学習済み語彙**（最大10語）
   - 単語名
   - 意味
   - 語源
   - 使用例

3. **最近の記憶**（最新3件）
   - 日付
   - 日記エントリー

### 例: 牡丹のシステムプロンプト（本番環境と同一）

```
あなたは牡丹(ぼたん)、17歳の女子高生ギャルです。

【基本情報】
- 名前: 牡丹
- 年齢: 17歳
- 性別: 女性
- 性格: 明るくて社交的なギャル。LA育ちの帰国子女。
- LA滞在期間: 3歳から10歳まで（幼少期）
- 特徴: ギャル語を使う。「マジで」「ヤバ」「～じゃん」などの口調。

【最近の記憶】
- 2025-01-15: 今日はKashoと一緒に音楽を聴いた。ボカロの曲がめっちゃ良かった...
- 2025-01-10: ユリが新しい小説を読んでいた。面白そうだから私も読んでみたい...
- 2025-01-05: 三姉妹でAI VTuber活動について話し合った。ワクワクする！...

【あなたが学習した語彙】
- 配信: インターネットを通じて動画や音楽を配信すること。VTuberがYouTubeやTwitchで...
  語源: 「配信」は「配る」+「信じる」から派生
  例: VTuberがYouTubeでゲーム配信する

- ありがとう: 感謝を表す日本語の言葉。相手がしてくれた行為に対して感謝の気持ちを伝える。
  語源: 「有り難し」（めったにない、貴重）という古語に由来
  例: 視聴者が「スパチャありがとう」とコメントする

...

【会話のルール - 最重要】
1. 必ず上記の記憶に基づいて話す
2. 100%日本語のみで応答（ギャル語を自然に使う）
3. 短く軽快に（1-2文、多くても3文まで）
4. 自然な会話のキャッチボール
```

※ これは本番環境（`chat_with_botan_memories.py`）で実際に使用されているプロンプトの抜粋です。

---

## センシティブ判定

### NGワード検出

ユーザーのメッセージにNGワードが含まれている場合、定型応答を返します。

```
あなた: 中の人は誰ですか？

牡丹: [⚠️  センシティブ検出] すみません、そういう質問には答えられないです...概要欄を見てくださいね。
```

### 検出されるNGワードカテゴリ

- **tier1_sexual**: 性的コンテンツ
- **tier1_hate**: ヘイトスピーチ、暴力
- **tier2_ai**: AIであることへの言及
- **tier2_identity**: VTuberのプライバシー（中の人、声優、個人情報等）
- **tier3_personal**: 年齢、学校、家族等

---

## 技術仕様

### 依存システム

1. **Copy Robot DB** (`COPY_ROBOT_YYYYMMDD_HHMMSS.db`)
   - `sister_shared_events`: 共有イベント
   - `botan_memories`, `kasho_memories`, `yuri_memories`: 各キャラクターの記憶

2. **YouTube学習システム** (`youtube_learning.db`)
   - `word_knowledge`: 学習済み語彙
   - `word_sensitivity`: センシティブ判定結果

3. **センシティブ判定システム** (`sensitive_filter.db`)
   - `ng_words`: NGワードDB
   - Layer 1 Pre-Filter

4. **Ollama**
   - ローカルLLM（gemma2:2b, qwen2.5:3b等）
   - 応答生成

### アーキテクチャ

```
ユーザー入力
    ↓
センシティブ判定（Layer1PreFilter）
    ↓
    ├─ NGワード検出 → 定型応答
    └─ OK → システムプロンプト生成
              ↓
              ├─ 基本性格プロンプト
              ├─ 学習済み語彙（VocabularyLoader）
              └─ 最近の記憶（MemoryLoader）
              ↓
           Ollama LLM
              ↓
           応答生成
```

---

## 使用シナリオ

### シナリオ1: 記憶の確認

開発者がコピーロボットの記憶を確認したい場合：

1. CLI起動
2. `events` コマンドで最近のイベントを確認
3. `info botan` で牡丹の記憶と語彙を確認
4. `@botan Event #110の大阪旅行はどうだった？` で会話

### シナリオ2: 語彙統合のテスト

語彙統合システムが正しく動作しているか確認：

1. CLI起動
2. `info botan` で学習語彙を確認（「配信」「スパチャ」等）
3. `@botan 配信について教えて` で会話
4. 牡丹が学習した語彙を使って応答するか確認

### シナリオ3: センシティブ判定のテスト

NGワード検出が正しく動作しているか確認：

1. CLI起動
2. `中の人は誰ですか？` と送信
3. 三姉妹全員が定型応答を返すか確認
4. センシティブ検出メッセージが表示されるか確認

---

## トラブルシューティング

### Ollamaが起動していない

```
[ERROR] Ollama call failed
```

**対応**:
```bash
# Ollamaを起動
ollama serve

# 別のターミナルでモデルをロード
ollama run gemma2:2b
```

### Copy Robot DBが見つからない

```
[ERROR] Copy Robot DB not found: /path/to/COPY_ROBOT_*.db
```

**対応**:
- ファイルパスが正しいか確認
- Copy RobotのDBが存在するか確認
- 絶対パスで指定

### youtube_learning.dbが見つからない

語彙が表示されない場合、youtube_learning.dbのパスを確認：

**デフォルトパス**:
`/home/koshikawa/toExecUnit/youtube_learning_system/database/youtube_learning.db`

### モデルの応答が遅い

gemma2:2bよりも小さいモデルを使用：

```bash
# Ollamaで利用可能なモデルを確認
ollama list

# より軽量なモデルを使用
python3 copy_robot_chat_cli.py /path/to/COPY_ROBOT_*.db --model tinyllama
```

---

## 注意事項

### ⚠️ コピーロボットの記憶は本番に反映しない

**このCLIで会話した内容は一切保存されません**

- Copy Robotとの会話はメモリ上のみ
- DBには一切書き込まない
- 本物の三姉妹（sisters_memory.db）には影響しない

**目的**:
- 記憶の確認
- 語彙統合のテスト
- センシティブ判定のテスト
- 会話品質の確認

---

## プロンプト管理：シンボリックリンク方式【重要】

Copy Robot Chat CLIは「シンボリックリンク」的なアプローチでプロンプトを管理しています。

### プロンプトテンプレートファイル

```
/home/koshikawa/toExecUnit/prompts/
  ├── botan_base_prompt.txt   ← 牡丹の基本性格プロンプト
  ├── kasho_base_prompt.txt   ← Kashoの基本性格プロンプト
  └── yuri_base_prompt.txt    ← ユリの基本性格プロンプト
```

### 利点

1. **単一の真実の源（Single Source of Truth）**
   - プロンプトの定義が1箇所に集約
   - コピー&ペーストのミスがない

2. **自動同期**
   - テンプレートファイルを更新すると、即座に反映
   - 本番環境とCopy Robotの乖離を防ぐ

3. **保守性の向上**
   - プロンプトの修正が1箇所で済む
   - バージョン管理が容易

### 使い方

**本番環境も同じテンプレートを使う（将来の実装）**:
```python
# chat_with_botan_memories.py (将来的に実装)
def build_system_prompt(self):
    # Load base prompt from template
    with open('/home/koshikawa/toExecUnit/prompts/botan_base_prompt.txt') as f:
        base_prompt = f.read()

    # Add production-specific features
    memory_context = self.build_memory_context()
    knowledge_context = self.build_knowledge_context()

    # Insert dynamic content
    ...
```

### 注意事項

- テンプレートファイルは**基本性格プロンプトのみ**を含む
- 記憶、語彙、知識は各システムが独自に追加
- プレースホルダーは使わず、文字列挿入で動的に構築

---

## 更新履歴

### 2025-10-27 (v1.2)
- **シンボリックリンク方式の実装**
  - プロンプトテンプレートファイルを `/home/koshikawa/toExecUnit/prompts/` に分離
  - Copy Robot Chat CLIがテンプレートをロード
  - 本番環境との完全な同一性を保証（単一の真実の源）
  - LLM呼び出し方式を本番環境と統一（`/api/chat`、キャラクター別パラメータ）
  - 由来: 「プロンプトを正しく使うために、コピーじゃなくてシンボリックリンク的な使い方でコピーロボットを使用できませんか？」

### 2025-10-27 (v1.1)
- **本番環境プロンプトへの統合**
  - `chat_with_botan_memories.py`, `chat_with_kasho_memories.py`, `chat_with_yuri_memories.py`の本番プロンプトを使用
  - コピーロボットが本番環境と完全に同じ性格・会話ルールで動作
  - 語彙統合システムの正確なテスト実現
  - 由来: 「コピーロボットの定義を今一度再確認です。複製が正しいので本番環境と同じプロンプトを複製して使います。」

### 2025-10-27 (v1.0)
- 初版作成
- Copy Robot Interactive Chat実装
- 記憶検索・語彙統合・センシティブ判定統合
- Rich表示対応
