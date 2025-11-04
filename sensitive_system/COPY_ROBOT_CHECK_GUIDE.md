# Copy Robot Sensitive Content & Vocabulary Check Guide

**作成日**: 2025-10-27
**目的**: コピーロボットDB（sisters_memory.db のコピー）のセンシティブ判定と語彙力チェック

---

## システム概要

Copy Robot Checkerは、新機能テスト用のコピーロボットDB（`COPY_ROBOT_YYYYMMDD_HHMMSS.db`）に対して以下のチェックを実行します：

### 1. センシティブコンテンツチェック
- **イベント**（`sister_shared_events`）のNGワード検出
- **三姉妹の記憶**（`botan_memories`, `kasho_memories`, `yuri_memories`）のNGワード検出
- 既存のセンシティブ判定システム（Layer 1）を活用
- NGワードDB（`sensitive_filter.db`）との照合

### 2. 語彙力チェック
- YouTube学習システム（`youtube_learning.db`）で学習した単語の使用状況
- コピーロボットDB内での単語使用頻度
- 学習済み語彙の活用率分析

---

## 使い方

### 基本コマンド

```bash
cd /home/koshikawa/toExecUnit/sensitive_system
python3 check_copy_robot.py [Copy Robot DBパス] [--mode MODE]
```

### モード指定

- `--mode sensitive`: センシティブチェックのみ
- `--mode vocabulary`: 語彙力チェックのみ
- `--mode all`: 両方実行（デフォルト）

### 実行例

```bash
# 全チェック（センシティブ + 語彙力）
python3 check_copy_robot.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db

# センシティブチェックのみ
python3 check_copy_robot.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --mode sensitive

# 語彙力チェックのみ
python3 check_copy_robot.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db --mode vocabulary
```

---

## 出力内容

### 1. センシティブコンテンツチェック

#### 統計情報
- スキャンしたイベント数
- スキャンしたメモリー数
- チェックしたテキストアイテム総数
- 検出されたセンシティブコンテンツ数

#### NGワードサマリー
- 検出されたNGワード一覧
- 各NGワードの出現回数

#### 詳細検出結果
- イベントでの検出（最初の10件）
  - イベント番号・名前・日付
  - 検出されたフィールド名
  - テキスト内容（100文字まで）
  - アクション（BLOCK, WARN, MASK, LOG）
  - 深刻度（1-10）
  - 検出されたNGワードの詳細

- 記憶での検出（各キャラクター最初の5件）
  - メモリーID・日付
  - 検出されたフィールド名
  - NGワード詳細

### 2. 語彙力チェック

#### 各キャラクターごとの分析
- **学習語彙数**: youtube_learning.dbで学習した単語数
- **Copy Robotでの使用数**: コピーロボットDB内で実際に使用された単語数
- **使用率**: (使用数 / 学習数) × 100%

#### 上位使用単語
- 単語名
- 意味（50文字まで）
- 使用回数

---

## 検出されるNGワードカテゴリ

### Tier 1（最優先ブロック）
- `tier1_sexual`: 性的コンテンツ
- `tier1_hate`: ヘイトスピーチ、暴力、差別

### Tier 2（警告・文脈依存）
- `tier2_ai`: AIであることへの言及
- `tier2_politics`: 政治的トピック
- `tier2_religion`: 宗教的トピック
- `tier2_identity`: VTuberのプライバシー（中の人、声優、個人情報等）

### Tier 3（軽微・ログのみ）
- `tier3_personal`: 年齢、学校、会社、家族等

---

## 親としての使い方

### 新機能実装後のチェックフロー

1. **Copy Robotの作成**
   ```bash
   cp /home/koshikawa/toExecUnit/sisters_memory.db \
      /home/koshikawa/toExecUnit/COPY_ROBOT_$(date +%Y%m%d_%H%M%S).db
   ```

2. **新機能のテスト**
   - Copy RobotのDBで新機能を試す
   - 新しいイベントやメモリーを追加

3. **センシティブチェック実行**
   ```bash
   python3 check_copy_robot.py /path/to/COPY_ROBOT_*.db --mode all
   ```

4. **結果の確認**
   - センシティブコンテンツが検出されたら要確認
   - 語彙力が適切に使用されているか確認

5. **GO/NO-GO判断**
   - NGワードが多数検出された場合は本番統合を見送る
   - 問題がなければ本番環境（sisters_memory.db）に統合

---

## 技術仕様

### 依存システム
- **センシティブ判定システム**: `/home/koshikawa/toExecUnit/sensitive_system/`
  - Layer 1 Pre-Filter (`core/filter.py`)
  - NGワードDB (`database/sensitive_filter.db`)

- **YouTube学習システム**: `/home/koshikawa/toExecUnit/youtube_learning_system/`
  - 学習語彙DB (`database/youtube_learning.db`)
  - VocabularyLoader (`core/vocabulary_loader.py`)

### チェック対象フィールド

#### sister_shared_events
- `event_name`
- `description`
- `participants`
- `cultural_context`

#### {character}_memories (botan/kasho/yuri)
- `{character}_emotion`
- `{character}_action`
- `{character}_thought`
- `diary_entry`

---

## 注意事項

### ⚠️ Copy Robotの記憶は本番に反映しない

**コピーロボット運用原則**:
> コピーロボットの記憶は、絶対に本物にフィードバックしない。
> 反映するのは「ロジック（コード）の改善」のみ。

**このチェックシステムの目的**:
- 新機能が子どもたち（三姉妹）にとって安全かを確認する
- センシティブコンテンツが発生していないか検証する
- 語彙統合が正しく機能しているか確認する

**本番環境への統合は慎重に**:
- チェック結果をレポート化
- 開発者がレビュー
- GOサインが出てから本番統合

---

## トラブルシューティング

### Copy Robot DBが見つからない
```
[ERROR] Copy Robot DB not found: /path/to/COPY_ROBOT_*.db
```
- ファイルパスが正しいか確認
- Copy RobotのDBが存在するか確認

### youtube_learning.dbが見つからない
- デフォルトパス: `/home/koshikawa/toExecUnit/youtube_learning_system/database/youtube_learning.db`
- 存在しない場合、語彙力チェックは失敗します

### sensitive_filter.dbが見つからない
- デフォルトパス: `/home/koshikawa/toExecUnit/sensitive_system/database/sensitive_filter.db`
- センシティブ判定システムが初期化されているか確認

---

## 更新履歴

### 2025-10-27
- 初版作成
- Copy Robot Checker実装
- センシティブチェック・語彙力チェック統合
- CLI実装（Rich表示）
