# Character Prompt Templates

**作成日**: 2025-10-27
**目的**: 三姉妹のプロンプトを単一の真実の源として管理

---

## 概要

このディレクトリには、牡丹・Kasho・ユリの基本性格プロンプトが含まれています。

これらのファイルは**シンボリックリンク的に**複数のシステムから参照されます：

- **Copy Robot Chat CLI** (`/home/koshikawa/toExecUnit/sensitive_system/copy_robot_chat_cli.py`)
- **本番環境**（将来実装）:
  - `chat_with_botan_memories.py`
  - `chat_with_kasho_memories.py`
  - `chat_with_yuri_memories.py`

---

## ファイル構成

```
prompts/
├── README.md                 ← このファイル
├── botan_base_prompt.txt     ← 牡丹の基本性格プロンプト
├── kasho_base_prompt.txt     ← Kashoの基本性格プロンプト
└── yuri_base_prompt.txt      ← ユリの基本性格プロンプト
```

---

## プロンプトの構造

各プロンプトファイルには以下が含まれます：

### 1. 基本情報
- 名前、年齢、性格、LA滞在期間など

### 2. 性格特性
- キャラクターごとの詳細な性格描写
- 行動パターン、思考傾向

### 3. 会話のルール
- 記憶の扱い方
- 言語・表現ルール
- 会話スタイル
- 会話例

---

## 使い方

### Copy Robot Chat CLI

```python
def _load_prompt_templates(self) -> Dict[str, str]:
    """Load character prompt templates from shared files"""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_files = {
        'botan': prompts_dir / "botan_base_prompt.txt",
        'kasho': prompts_dir / "kasho_base_prompt.txt",
        'yuri': prompts_dir / "yuri_base_prompt.txt"
    }

    prompts = {}
    for character, filepath in prompt_files.items():
        with open(filepath, 'r', encoding='utf-8') as f:
            prompts[character] = f.read()

    return prompts
```

### 動的コンテンツの追加

基本プロンプトに、システム固有の動的コンテンツを追加します：

```python
def generate_system_prompt(self, character: str) -> str:
    # Load base prompt from template
    base_prompt = self.base_prompts[character]

    # Build dynamic sections
    memory_section = self.build_memory_section(character)
    vocab_section = self.build_vocabulary_section(character)

    # Insert before "会話のルール"
    rules_marker = "【会話のルール - 最重要】"
    if rules_marker in base_prompt:
        parts = base_prompt.split(rules_marker)
        prompt = parts[0] + memory_section + vocab_section + "\n" + rules_marker + parts[1]

    return prompt
```

---

## 編集ガイドライン

### ✅ 編集すべきこと

- 基本性格の修正
- 会話ルールの追加・変更
- 会話例の更新

### ❌ 編集すべきでないこと

- 記憶や語彙の挿入（動的コンテンツ）
- システム固有の機能追加
- プレースホルダーの使用

### 編集時の注意事項

1. **テストを必ず実施**
   - Copy Robot Chat CLIで動作確認
   - 本番環境でも確認（将来実装後）

2. **バックアップを取る**
   - 編集前にコピーを保存
   - Git commitで履歴を残す

3. **一貫性を保つ**
   - 3人のプロンプト構造を統一
   - フォーマットを揃える

---

## シンボリックリンク方式の利点

### 1. 単一の真実の源（Single Source of Truth）
- プロンプトの定義が1箇所に集約
- コピー&ペーストのミスがない
- バージョン管理が容易

### 2. 自動同期
- テンプレートファイルを更新すると、即座に反映
- 本番環境とCopy Robotの乖離を防ぐ

### 3. 保守性の向上
- プロンプトの修正が1箇所で済む
- 影響範囲が明確

---

## トラブルシューティング

### プロンプトファイルが見つからない

```
[ERROR] プロンプトファイルが見つかりません: /home/koshikawa/toExecUnit/prompts/botan_base_prompt.txt
```

**対応**:
1. ファイルパスを確認
2. ファイルが存在するか確認
3. 読み取り権限があるか確認

### プロンプトが反映されない

**対応**:
1. システムを再起動
2. キャッシュをクリア
3. ファイルの文字コードを確認（UTF-8）

---

## 更新履歴

### 2025-10-27
- 初版作成
- 牡丹、Kasho、ユリのプロンプトテンプレートを作成
- シンボリックリンク方式の導入

---

**由来**: 「プロンプトを正しく使うために、コピーじゃなくてシンボリックリンク的な使い方でコピーロボットを使用できませんか？」

これにより、Copy Robotは真の意味で「本番環境のコピー」になりました。
