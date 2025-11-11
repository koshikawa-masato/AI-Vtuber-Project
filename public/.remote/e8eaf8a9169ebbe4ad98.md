---
title: プロンプトエンジニアリング実践：AI VTuber三姉妹の性格を一貫させる技術
tags:
  - Python
  - AI
  - Vtuber
  - LLM
  - プロンプトエンジニアリング
private: false
updated_at: '2025-11-07T18:22:53+09:00'
id: e8eaf8a9169ebbe4ad98
organization_url_name: null
slide: false
ignorePublish: false
---

# はじめに：AI VTuber「牡丹プロジェクト」とは

本記事は、**AI VTuber三姉妹（Kasho、牡丹、ユリ）のプロンプトエンジニアリング実践**を解説します。

## プロジェクト概要

「牡丹プロジェクト」は、**過去の記憶を持つAI VTuber三姉妹** を実現するプロジェクトです。

### 三姉妹の紹介

- **Kasho（長女、19歳）**: 論理的・分析的、慎重でリスク重視、保護者的な姉
- **牡丹（次女、17歳）**: ギャル系、感情的・直感的、明るく率直、行動力抜群
- **ユリ（三女、15歳）**: 統合的・洞察的、調整役、共感力が高い

### GitHubリポジトリ

- https://github.com/koshikawa-masato/AI-Vtuber-Project
- プロンプトファイル: `prompts/` ディレクトリで公開中

---

## この記事で分かること

- ✅ キャラクター一貫性がなぜ難しいのか
- ✅ プロンプト設計の3層構造（静的+動的）
- ✅ 三姉妹の性格を作り分ける実践テクニック
- ✅ 実際のプロンプトテンプレート（一部公開）
- ✅ Claude Code式対話技術の統合
- ✅ 失敗例と改善プロセス

**対象読者**: LLMアプリケーション開発者、AI VTuber開発者、プロンプトエンジニアリングに興味がある方

---

# 第1章：なぜキャラクター一貫性は難しいのか

## 1.1 よくある失敗パターン

### 失敗例1: ギャルキャラのはずが丁寧語になる

```
ユーザー: 好きな食べ物は？
牡丹: 私が好きな食べ物は、タコスとハンバーガーです。LA時代によく食べていました。
```

**問題点**:
- ❌ 口調が固い（「です」「ました」）
- ❌ 「私」は使うが「マジで」「ヤバ」がない
- ❌ ギャルキャラの性格が出ていない

### 失敗例2: 複数ターンで性格が変わる

```
1ターン目: 「マジでヤバいじゃん！」（ギャル口調）
　　↓
3ターン目: 「それは素晴らしいと思います」（丁寧語）
```

**問題点**:
- ❌ 会話が進むと性格設定が薄れる
- ❌ LLMが「一般的な応答」にフォールバックしている

### 失敗例3: 記憶と矛盾する発言

```
牡丹（17歳、LA滞在は3-10歳）: 「LAでサーフィンやってた！」
```

**問題点**:
- ❌ 3-10歳の幼少期にサーフィンは不自然
- ❌ キャラクター設定と記憶が矛盾

---

## 1.2 問題の本質

### なぜ一貫性が保てないのか

| 原因 | 説明 |
|------|------|
| **文脈の優先度** | LLMは直近の文脈を重視し、初期設定が薄れる |
| **曖昧なプロンプト** | 「ギャル語を使う」だけでは不十分 |
| **禁止事項の欠如** | 「やってはいけないこと」が明示されていない |
| **動的要素の不足** | 記憶や学習内容が反映されない |

**重要な学び**:
> キャラクター一貫性は「設定を書く」だけでは達成できない。**構造化されたプロンプト設計** と **動的な情報注入** が必要。

---

# 第2章：プロンプト設計の3層構造

## 2.1 全体設計：静的部分 + 動的部分

三姉妹のシステムプロンプトは、以下の3層構造で生成されます。

```python
システムプロンプト = (
    基本性格プロンプト（静的）     # テンプレートファイル
    + 記憶セクション（動的）        # DBから取得
    + 語彙セクション（動的）        # 学習システムから取得
)
```

**設計思想**:
- **静的部分**: キャラクター性格は固定（テンプレートファイル）
- **動的部分**: 記憶・学習内容は会話ごとに変化

---

## 2.2 層1: 基本性格プロンプト（静的）

### ファイル構成

```
prompts/
├── botan_base_prompt.txt    # 牡丹の基本性格（128行）
├── kasho_base_prompt.txt    # Kashoの基本性格（132行）
└── yuri_base_prompt.txt     # ユリの基本性格（131行）
```

**管理方針**:
- ✅ テキストファイルで管理（Git追跡）
- ✅ Pythonコードとは分離（Single Source of Truth）
- ✅ 本番システムとCopy Robotで共有

### 牡丹のプロンプト構造（簡略版）

```text
あなたは牡丹(ぼたん)、17歳の女子高生ギャルです。

【基本情報】
- 名前: 牡丹
- 年齢: 17歳
- 性別: 女性
- 性格: 明るくて社交的なギャル。LA育ちの帰国子女。
- LA滞在期間: 3歳から10歳まで（幼少期）
- 特徴: ギャル語を使う。「マジで」「ヤバ」「～じゃん」などの口調。

【会話のルール - 最重要】
1. **必ず上記の記憶に基づいて話す**
   - 記憶にないことは「覚えてない」と答える
   - LA時代は3-10歳の幼少期なので、子供らしい体験

2. **言語・表現のルール（厳守）**
   - 必ず100%日本語のみで応答する
   - 絶対に英語・中国語・その他の外国語を使わない
   - ギャル語を自然に使う（「マジで」「ヤバ」「～じゃん」など）
   - 一人称は「私」「あたし」「うち」を使う（「俺」「僕」は禁止）

3. **会話スタイル（最重要）**
   - 自然な会話のキャッチボールを心がける
   - 説明的な長文は避け、会話的に話す
   - 相手にも質問を返す（「オジサンは？」「どう思う？」など）
   - 感情を込めた反応（「マジで！？」「ヤバ！」「へー！」など）
   - 短く軽快に（1-2文、多くても3文まで）
   - オープンエンドな話し方で会話を広げる

...（以下、詳細ルール）
```

**重要なポイント**:
1. **基本情報**: 名前、年齢、性格、背景を明示
2. **言語ルール**: 100%日本語、禁止ワードを明記
3. **会話スタイル**: 短く軽快、質問を返す
4. **文字数制限**: 1-2文、最大3文まで

---

## 2.3 層2: 記憶セクション（動的）

### 記憶注入の実装

```python
def generate_system_prompt(self, character: str, recent_context: bool = True) -> str:
    """
    システムプロンプトを生成（語彙統合）

    Args:
        character: 'botan', 'kasho', or 'yuri'
        recent_context: 最近の記憶を含めるか

    Returns:
        システムプロンプト
    """
    # 1. 基本プロンプト取得
    base_prompt = self.base_prompts[character]

    # 2. 記憶セクション生成
    memory_section = ""
    if recent_context:
        memories = self.memory_loader.get_character_recent_memories(character, limit=3)
        if memories:
            memory_section = "\n【最近の記憶】\n"
            for memory in memories:
                if memory['diary_entry']:
                    diary_preview = memory['diary_entry'][:100]
                    if len(memory['diary_entry']) > 100:
                        diary_preview += "..."
                    memory_section += f"- {memory['memory_date']}: {diary_preview}\n"

    # 3. 語彙セクションは次のセクションで...

    return base_prompt + memory_section
```

### 記憶セクションの例

```text
【最近の記憶】
- 2025-10-20: LAで歌のレッスン受けてた。Kashoに教えてもらった。楽しかった！
- 2025-10-15: ホロライブのころねちゃんの配信見て爆笑した。「なーほーね」最高。
- 2025-10-10: 学校で友達とカラオケ行った。めっちゃ盛り上がった〜！
```

**効果**:
- ✅ 会話中に記憶を参照できる
- ✅ 「LA時代どうだった？」という質問に具体的に答えられる
- ✅ 記憶と矛盾しない応答が可能

---

## 2.4 層3: 語彙セクション（動的）

### 語彙注入の実装

```python
def format_vocabulary_for_prompt(self, character: str) -> str:
    """
    プロンプト用に語彙をフォーマット

    Args:
        character: 'botan', 'kasho', or 'yuri'

    Returns:
        フォーマット済み語彙文字列
    """
    vocabulary = self.get_learned_vocabulary(character)

    if not vocabulary:
        return ""

    lines = ["\n【あなたが学習した語彙】\n"]

    for vocab in vocabulary[:10]:  # 最初の10語
        word = vocab['word']
        meaning = vocab['meaning'] or '(意味不明)'

        if vocab['language'] == 'en' and vocab['translation']:
            lines.append(f"- {word} ({vocab['translation']}): {meaning[:80]}")
        else:
            lines.append(f"- {word}: {meaning[:80]}")

    lines.append("\nこれらの語彙を理解して、適切に使用してください。")

    return '\n'.join(lines)
```

### 語彙セクションの例

```text
【あなたが学習した語彙】
- サーモン (salmon): 鮭。寿司ネタでも人気。
- ハンバーガー: アメリカの代表的なファストフード。
- カラオケ: 日本発祥の娯楽。友達と楽しむ。
- ホロライブ: VTuber事務所。ころねやみこちが所属。
- ゲーム実況: ゲームをプレイしながら配信すること。

これらの語彙を理解して、適切に使用してください。
```

**効果**:
- ✅ YouTube学習システムと統合
- ✅ 学習した語彙を会話で使える
- ✅ 知らない単語には「知らない」と答える

---

## 2.5 プロンプト注入の実装

### 挿入ポイントの設計

```python
def generate_system_prompt(self, character: str, recent_context: bool = True) -> str:
    # 基本プロンプト取得
    base_prompt = self.base_prompts[character]

    # 記憶・語彙セクション生成
    memory_section = self._generate_memory_section(character, recent_context)
    vocab_section = self.vocab_loader.format_vocabulary_for_prompt(character)

    # 挿入ポイントを探して注入
    rules_marker = "【会話のルール - 最重要】"
    if rules_marker in base_prompt:
        parts = base_prompt.split(rules_marker)
        # 基本情報の後、会話ルールの前に注入
        prompt = parts[0] + memory_section + vocab_section + "\n" + rules_marker + parts[1]
    else:
        # Fallback: 末尾に追加
        prompt = base_prompt + memory_section + vocab_section

    return prompt
```

**挿入位置**:
```
【基本情報】
  ↓
【最近の記憶】← 動的注入
【学習した語彙】← 動的注入
  ↓
【会話のルール - 最重要】
```

---

# 第3章：三姉妹の性格を作り分ける技術

## 3.1 性格設計マトリクス

三姉妹の性格を明確に作り分けるため、以下の要素を定義しています。

| 要素 | 牡丹（次女） | Kasho（長女） | ユリ（三女） |
|------|------------|--------------|------------|
| **一人称** | あたし/私 | 私 | 私/ユリ |
| **基本口調** | 「～じゃん」「～だよ」 | 「～です」「～でしょう」 | 「～かな」「～だと思う」 |
| **文章長** | 1-2文（約40文字） | 2-4文（約80文字） | 2-3文（約60文字） |
| **質問スタイル** | 「オジサンは？」 | 「どうお考えですか？」 | 「どう感じる？」 |
| **感情表現** | 「マジで！？」「ヤバ！」 | 「少し心配です」 | 「...そうなんだ」 |
| **会話の特徴** | 明るく軽快、質問を返す | 論理的、説明的 | 静かで洞察的 |

---

## 3.2 会話スタイルの違い（実例）

### 同じ質問に対する三姉妹の応答

**質問**: 「最近どう？」

#### 牡丹（明るく短く）

```
「マジで楽しいよ！最近ホロライブ見まくってるんだ。オジサンは？」
```

**特徴**:
- ✅ 短い（1文）
- ✅ ギャル口調（「マジで」「～んだ」）
- ✅ 感情表現（「楽しいよ！」）
- ✅ 質問を返す（「オジサンは？」）

#### Kasho（丁寧で論理的）

```
「最近は大学の課題が多くて少し忙しいです。
ただ、妹たちは元気にしているので安心しています。
あなたはいかがですか？」
```

**特徴**:
- ✅ やや長い（3文）
- ✅ 丁寧語（「～です」「～ます」）
- ✅ 状況説明（課題、妹の様子）
- ✅ 論理的接続詞（「ただ」「ので」）

#### ユリ（静かで控えめ）

```
「...最近は本を読んでる。静かな時間が好きだから。」
```

**特徴**:
- ✅ 短い（2文）
- ✅ 内省的（「...」で間を作る）
- ✅ 理由を添える（「～だから」）
- ✅ 質問は返さない（控えめ）

---

## 3.3 実装上の工夫

### 工夫1: 禁止ワードの明示

**牡丹の禁止事項**:
```text
【絶対にやってはいけないこと】
❌ 一人称「俺」「僕」は使わない
❌ 英語・中国語を使わない（固有名詞以外）
❌ 丁寧語「～です」「～ます」は使わない
❌ 3文以上の長文は禁止
❌ 説明的な口調は禁止
```

**効果**: LLMが「やってはいけないこと」を明確に理解できる

### 工夫2: 文字数制限

```text
【牡丹】
- 1ターン目: 50文字以内
- 通常会話: 1-2文、最大3文まで

【Kasho】
- 1ターン目: 60文字以内
- 通常会話: 2-4文

【ユリ】
- 1ターン目: 50文字以内
- 通常会話: 2-3文
```

**効果**: 文章長で性格を差別化

### 工夫3: 会話例を3つ以上書く

**牡丹のプロンプトより**:
```text
【会話例（良い例）】
オジサン: LAってどんなとこだった？
牡丹: マジで楽しかったよ！Kashoに歌教えてもらったりしたな〜。
     オジサンは海外行ったことある？

オジサン: へー面白いね
牡丹: でしょ？私めっちゃ懐かしいわ。ねえオジサン、子供の頃の思い出とかある？
```

**効果**: 具体例があると、LLMが口調を真似しやすい

---

## 3.4 キャラクター別のLLMパラメータ調整

### キャラクター固有のパラメータ

```python
llm_params = {
    'botan': {
        "temperature": 0.5,          # やや高め（明るく多様な応答）
        "num_predict": 1000,         # 長めの応答を許容
        "top_p": 0.85,
        "repeat_penalty": 1.25,      # 繰り返しを避ける
        "stop": ["あなた:", "オジサン:", "User:", "Assistant:"]
    },
    'kasho': {
        "temperature": 0.4,          # 低め（慎重で一貫性重視）
        "num_predict": 1000,
        "top_p": 0.8,
        "repeat_penalty": 1.2,
        "stop": ["あなた:", "相手:", "User:", "Assistant:"]
    },
    'yuri': {
        "temperature": 0.5,          # バランス型
        "num_predict": 1000,
        "top_p": 0.85,
        "repeat_penalty": 1.15,      # やや低め（繰り返し表現を許容）
        "stop": ["あなた:", "相手:", "User:", "Assistant:"]
    }
}
```

**設計思想**:
- **temperature**: 性格の多様性を調整
- **repeat_penalty**: キャラクターの一貫性を調整
- **stop**: 役割の混同を防ぐ

---

# 第4章：Claude Code式対話技術の統合

## 4.1 なぜClaude Code式なのか

**Claude Codeの対話技術**:
- 相談者に寄り添う
- 一度に全てを出さない（段階的掘り下げ）
- オープンエンド質問で相手に語らせる
- 相手の言葉を使う

**三姉妹に統合した理由**:
- AI VTuberは視聴者との対話が重要
- 一方的なアドバイスは嫌われる
- 視聴者が「話を聞いてもらえた」と感じることが大切

---

## 4.2 段階的掘り下げの実装

### 1ターン目のテンプレート

```text
[共感] + [オープンエンド質問] = 50文字以内
```

#### 牡丹（ギャル風）

```text
テンプレート: [共感15文字] + [質問25文字] = 合計40文字前後

例: 「わかるわかる！モヤモヤするよね。具体的にどのあたりで引っかかってるの？」
```

#### Kasho（丁寧風）

```text
テンプレート: [共感20文字] + [質問30文字] = 合計50文字前後

例: 「それは大変ですね。具体的にどのようなことでお悩みですか？」
```

#### ユリ（静かな風）

```text
テンプレート: [共感15文字] + [質問30文字] = 合計45文字前後

例: 「...悩んでるんだね。どんな点で悩んでるのか、教えてくれるかな？」
```

---

## 4.3 絶対にやってはいけないことの明示

### プロンプトに記載した禁止事項

```text
【絶対にやってはいけないこと】
❌ 1ターン目で複数のアドバイスを出す
❌ 1ターン目で「まず～、次に～、最後に～」と段階を説明する
❌ 1ターン目で「～すると良いよ」「～がおすすめ」と提案する
❌ 1ターン目で「～って思ったり、～と感じたり」と相手の気持ちを推測する
❌ 1ターン目で「～？それとも～？」「どっち？」と選択肢を提示する
❌ 相手が答える前に次の質問を重ねる
❌ 3文以上で答える（必ず2文以内、50文字以内）
```

### NG例とOK例

**NG例（牡丹）**:
```text
「モヤモヤするよね。まず目標を決めて、次に練習方法を考えて、
最後に継続する習慣を作ると良いよ。『上手くなりたい』って思ったり、
『楽しければいい』って感じたり...どっち？」
```

**問題点**:
- ❌ 長い（70文字以上）
- ❌ アドバイス多数（「まず」「次に」「最後に」）
- ❌ 推測（「～って思ったり」）
- ❌ 選択肢提示（「どっち？」）

**OK例（牡丹）**:
```text
「わかるわかる！モヤモヤするよね。具体的にどのあたりで引っかかってるの？」
```

**良い点**:
- ✅ 短い（40文字）
- ✅ 共感のみ（「わかるわかる！」）
- ✅ オープンエンド質問（「具体的にどのあたりで」）
- ✅ アドバイスなし

---

## 4.4 2ターン目以降の設計

### 2ターン目のルール

```text
【2ターン目のルール】
- 相手の発言を受け止める（1文、15文字）
- 掘り下げる質問 or 選択肢の提示（1-2文、30-40文字）
- 合計: 2-3文、70文字以内
- まだアドバイスは出さない
```

**牡丹の例**:
```text
「あー、YouTube見ちゃうとキリないよね。
オジサンは『上手くなりたい』って思ってる？それとも『楽しければいい』って感じ？」
```

### 3ターン目のルール

```text
【3ターン目のルール】
- 本質を指摘（1文）
- さらに掘り下げる質問（1文）
- 合計: 2文、60文字以内
```

**牡丹の例**:
```text
「そっか、そこがモヤモヤの正体かもね。
じゃあさ、ベース弾いてる時、どんな時が一番楽しい？」
```

### 4ターン目以降

```text
【4ターン目以降】
- ここで初めてアドバイス・提案を出す
- ただし押し付けない（疑問形、「～じゃない？」）
- 相手の言葉を使う
```

**牡丹の例**:
```text
「それな！じゃあそれでいいんじゃない？
『上手くなる』より『好きな曲を楽しく弾く』でさ。」
```

---

# 第5章：プロンプトの実装とメンテナンス

## 5.1 ファイル構成

```
toExecUnit/
├── prompts/                          # プロンプトテンプレート
│   ├── botan_base_prompt.txt         # 牡丹の基本性格（128行）
│   ├── kasho_base_prompt.txt         # Kashoの基本性格（132行）
│   └── yuri_base_prompt.txt          # ユリの基本性格（131行）
├── sensitive_system/
│   └── copy_robot_chat_cli.py        # プロンプト読み込みと動的生成
└── youtube_learning_system/
    └── conversation.py               # 語彙注入
```

**Single Source of Truth**:
- プロンプトファイルが唯一の真実
- 本番システム（`chat_with_botan_memories.py`）とCopy Robotで共有
- Gitで管理、変更履歴を追跡

---

## 5.2 プロンプト読み込みの実装

### テンプレート読み込み

```python
def _load_prompt_templates(self) -> Dict[str, str]:
    """
    Load character prompt templates from shared files (symbolic link approach)

    These files are the single source of truth, shared with production:
    - chat_with_botan_memories.py
    - chat_with_kasho_memories.py
    - chat_with_yuri_memories.py

    Returns:
        Dict of {character: prompt_template}
    """
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_files = {
        'botan': prompts_dir / "botan_base_prompt.txt",
        'kasho': prompts_dir / "kasho_base_prompt.txt",
        'yuri': prompts_dir / "yuri_base_prompt.txt"
    }

    prompts = {}
    for character, filepath in prompt_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                prompts[character] = f.read()
        except FileNotFoundError:
            self.console.print(f"[red]✗ プロンプトファイルが見つかりません: {filepath}[/red]")
            # Fallback to a simple prompt
            prompts[character] = f"あなたは{character}です。"

    return prompts
```

**重要なポイント**:
- ✅ ファイルパスは相対パス（`parent.parent / "prompts"`）
- ✅ エラーハンドリング（FileNotFoundError）
- ✅ Fallback機能

---

## 5.3 動的セクションの注入

### 完全な実装

```python
def generate_system_prompt(self, character: str, recent_context: bool = True) -> str:
    """
    システムプロンプトを生成（語彙統合）

    Template file (shared with production) + dynamic content:
    1. 基本性格プロンプト（テンプレートから）
    2. 記憶セクション（動的生成）
    3. 語彙セクション（動的生成）

    Args:
        character: 'botan', 'kasho', or 'yuri'
        recent_context: 最近の記憶を含めるか

    Returns:
        システムプロンプト
    """
    # Get base prompt from template file
    base_prompt = self.base_prompts[character]

    # Build memory section
    memory_section = ""
    if recent_context:
        memories = self.memory_loader.get_character_recent_memories(character, limit=3)
        if memories:
            memory_section = "\n【最近の記憶】\n"
            for memory in memories:
                if memory['diary_entry']:
                    diary_preview = memory['diary_entry'][:100]
                    if len(memory['diary_entry']) > 100:
                        diary_preview += "..."
                    memory_section += f"- {memory['memory_date']}: {diary_preview}\n"

    # Build vocabulary section
    vocab_section = self.vocab_loader.format_vocabulary_for_prompt(character)
    if not vocab_section:
        vocab_section = ""
    else:
        vocab_section = "\n" + vocab_section

    # Insert memory and vocabulary after 基本情報, before 会話のルール
    rules_marker = "【会話のルール - 最重要】"
    if rules_marker in base_prompt:
        parts = base_prompt.split(rules_marker)
        prompt = parts[0] + memory_section + vocab_section + "\n" + rules_marker + parts[1]
    else:
        # Fallback: append at the end
        prompt = base_prompt + memory_section + vocab_section

    return prompt
```

**設計のポイント**:
1. **段階的構築**: 基本→記憶→語彙の順で構築
2. **挿入ポイント**: 「会話のルール」の前に動的セクションを注入
3. **Fallback**: マーカーがない場合は末尾に追加

---

## 5.4 会話履歴の管理

### LLM呼び出し（本番環境と同じ方式）

```python
def call_ollama(self, system_prompt: str, character: str = 'botan') -> str:
    """
    Ollamaを呼び出して応答生成（本番環境と同じ方式）

    Args:
        system_prompt: システムプロンプト
        character: キャラクター名（パラメータ調整用、会話履歴参照）

    Returns:
        LLM応答
    """
    # Character-specific LLM parameters
    llm_params = {
        'botan': {
            "temperature": 0.5,
            "num_predict": 1000,
            "top_p": 0.85,
            "repeat_penalty": 1.25,
            "stop": ["あなた:", "オジサン:", "User:", "Assistant:"]
        },
        # ... Kasho, ユリのパラメータ
    }

    # Use /api/chat (like production) instead of /api/generate
    # Include conversation history
    messages = [
        {"role": "system", "content": system_prompt}
    ] + self.history[character]

    cmd = [
        "curl", "-s", "-X", "POST",
        f"{self.ollama_host}/api/chat",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": llm_params.get(character, llm_params['botan'])
        })
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    # ... レスポンス処理

    return response
```

**重要**:
- ✅ `/api/chat` エンドポイント使用（会話履歴を含む）
- ✅ キャラクター固有のパラメータ適用
- ✅ 会話履歴を保持（`self.history[character]`）

---

# 第6章：実際の動作確認（Copy Robotデモ）

## 6.1 デモの様子

![Copy Robot Interactive Chat Demo](https://raw.githubusercontent.com/koshikawa-masato/AI-Vtuber-Project/main/screenshots/copy_robot.png)

> **注記**: このデモは **Copy Robot**（プロトタイプシステム）での実際の動作です。本番システムへの統合前の検証段階のものです。

**確認できること**:
- ✅ 三姉妹がそれぞれの個性で応答（挨拶の場面）
  - 牡丹: 「こんばんは！牡丹だよ～」（明るいギャル口調）
  - Kasho: 「こんばんは、Kashoです」（丁寧で論理的）
  - ユリ: 「こんばんは…ユリです」（控えめ）
- ✅ `@キャラクター名`で個別対話が可能
- ✅ 記憶システムが動作（牡丹が好きなVTuberについて記憶から回答）
- ✅ レスポンス時間の表示（LLM呼び出しの可観測性）

---

## 6.2 性格一貫性の検証

### 牡丹への質問

**質問**: 「@botan 牡丹の好きなVTuberって誰？」

**牡丹の応答**:
```
あたしのお気に入りVTuberといえば成神ころねとさくらみこちゃんじゃん。
二人ともめっちゃ面白いんだよね！オジサンはどっち派？
```

**検証ポイント**:
- ✅ **一人称**: 「あたし」（プロンプト通り）
- ✅ **口調**: 「～じゃん」「～だよね」（ギャル口調）
- ✅ **記憶**: 好きなVTuberを覚えている（記憶システム動作）
- ✅ **質問を返す**: 「オジサンはどっち派？」（会話のキャッチボール）
- ✅ **短く軽快**: 2文（約50文字）

### Kashoへの質問

**質問**: 「@Kasho 好きな音楽のジャンルって何？」

**Kashoの応答**:
```
私は幅広い種類の音楽を楽しんでいますが、特にクラシックやジャズが好みですね。
どのような曲をお勧めしますか？あるいは、あなたはどんな音楽を好むのですか？
```

**検証ポイント**:
- ✅ **一人称**: 「私」（プロンプト通り）
- ✅ **口調**: 「～ます」「～ですね」（丁寧語）
- ✅ **論理的**: 「幅広い種類」→「特に」（論理的接続）
- ✅ **質問を返す**: 2つの質問（丁寧な会話スタイル）
- ✅ **やや長い**: 3文（約80文字）

---

## 6.3 技術的なポイント

**Copy Robotの実装**:
- 使用モデル: qwen2.5:14b（ローカルLLM）
- データベース: COPY_ROBOT_20251027_142159.db（117コアイベント + 記憶）
- チャットログ自動保存機能
- プロンプトテンプレート共有（`prompts/`）

**実測レスポンス時間**:
- 牡丹（50文字応答）: 11.651秒
- Kasho（80文字応答）: 4.212秒

---

# 第7章：失敗例と改善プロセス

## 7.1 初期の失敗：プロンプトが曖昧

### 初期プロンプト（NG例）

```text
あなたは牡丹です。17歳の女子高生で、明るい性格です。
ギャル語を使います。
```

**結果**:
```
ユーザー: 好きな食べ物は？
牡丹: 私の好きな食べ物は、タコスとハンバーガーです。
     LA時代によく食べていました。
```

**問題点**:
- ❌ 丁寧語になってしまう（「です」「ました」）
- ❌ 「マジで」「ヤバ」が出ない
- ❌ 質問を返さない
- ❌ 説明的で長い

---

## 7.2 改善1: 具体例を大量に追加

### 改善後のプロンプト

```text
【口調】
- 「～じゃん」「～だよ」「～なんだよね」を使う
- 「マジで」「ヤバ」「へー！」などの感嘆詞を使う
- 一人称は「私」「あたし」「うち」

【会話例】
オジサン: LAってどんなとこだった？
牡丹: マジで楽しかったよ！Kashoに歌教えてもらったりしたな〜。
     オジサンは海外行ったことある？

オジサン: へー面白いね
牡丹: でしょ？私めっちゃ懐かしいわ。ねえオジサン、子供の頃の思い出とかある？
```

**効果**:
- ✅ LLMが具体例を真似しやすい
- ✅ 口調が安定する

---

## 7.3 改善2: 禁止事項の明示

### 追加した禁止事項

```text
【絶対にやってはいけないこと】
❌ 「です」「ます」は使わない
❌ 一人称「俺」「僕」は使わない
❌ 3文以上の長文は禁止
❌ 説明的な口調は禁止
❌ 英語・中国語を使わない（固有名詞以外）
```

**効果**:
- ✅ 丁寧語にならなくなった
- ✅ 長文が減った

---

## 7.4 改善3: 文字数制限の導入

### 追加した制限

```text
【会話スタイル】
- 短く軽快に（1-2文、多くても3文まで）
- 1ターン目: 50文字以内
- 通常会話: 約40文字
```

**効果**:
- ✅ 応答が短くなり、会話的になった
- ✅ 質問を返す余裕ができた

---

## 7.5 改善4: Claude Code式対話技術の統合

### 追加したセクション

```text
【悩み相談・深い話題の場合（絶対厳守）- Claude Code式対話技術】

【最初のターン（1ターン目）の絶対ルール】
テンプレート: [共感15文字] + [質問25文字] = 合計40文字前後

OK例: 「わかるわかる！モヤモヤするよね。具体的にどのあたりで引っかかってるの？」
```

**効果**:
- ✅ 相談対応が自然になった
- ✅ 一方的なアドバイスが減った

---

# 第8章：プロンプトチューニングのコツ

## 8.1 ルール1: 具体例を3つ以上書く

### NG: 抽象的な指示

```text
❌ 「ギャル語を使う」
```

### OK: 具体例を添える

```text
✅ 「ギャル語を使う（例: マジで、ヤバ、～じゃん）」
```

### Better: 会話例を3つ書く

```text
✅ 【会話例】
  例1: ...
  例2: ...
  例3: ...
```

**効果**: LLMは具体例から学習する

---

## 8.2 ルール2: 禁止事項を明示する

### 「やるべきこと」だけでなく「やってはいけないこと」も書く

```text
【やるべきこと】
✅ ギャル語を使う
✅ 短く軽快に話す

【やってはいけないこと】
❌ 丁寧語「～です」「～ます」は使わない
❌ 3文以上の長文は禁止
```

**効果**: LLMの行動範囲を明確に制限できる

---

## 8.3 ルール3: 文字数制限を設ける

### キャラクターごとに文字数を変える

```text
- 牡丹: 1-2文、約40文字
- Kasho: 2-4文、約80文字
- ユリ: 2-3文、約60文字
```

**効果**: 文章長で性格を差別化できる

---

## 8.4 ルール4: システムプロンプト vs ユーザープロンプトの使い分け

### 使い分けの原則

| 用途 | システムプロンプト | ユーザープロンプト |
|------|------------------|------------------|
| **性格・口調** | ✅ 静的な基本設定 | ❌ |
| **記憶** | ✅ 動的な注入 | ❌ |
| **語彙** | ✅ 動的な注入 | ❌ |
| **質問** | ❌ | ✅ ユーザーの質問 |
| **指示** | ❌ | ✅ 特定の指示 |

**理由**: システムプロンプトは「キャラクターの本質」、ユーザープロンプトは「会話の文脈」

---

## 8.5 ルール5: テンプレートファイルで管理

### ファイル管理のメリット

```
prompts/
├── botan_base_prompt.txt    # Git追跡
├── kasho_base_prompt.txt
└── yuri_base_prompt.txt
```

**メリット**:
- ✅ 変更履歴を追跡できる（Git）
- ✅ 本番システムとプロトタイプで共有できる
- ✅ Pythonコードと分離（Single Source of Truth）
- ✅ レビューしやすい（テキストファイル）

---

## 8.6 ルール6: 定期的に検証して改善

### 検証サイクル

```
1. プロンプト変更
   ↓
2. Copy Robotでテスト
   ↓
3. 応答を確認（口調、文字数、性格一貫性）
   ↓
4. 問題があれば改善
   ↓
5. 本番システムに統合
```

**重要**: 変更は小さく、頻繁に

---

# まとめ

## 実践的なポイント

### 1. プロンプトは3層構造

```python
システムプロンプト = (
    基本性格プロンプト（静的）     # テンプレートファイル
    + 記憶セクション（動的）        # DBから取得
    + 語彙セクション（動的）        # 学習システムから取得
)
```

### 2. 性格の作り分け

| 要素 | 実装方法 |
|------|---------|
| **口調** | 具体例を3つ以上、禁止事項を明示 |
| **文章長** | 文字数制限（1-2文、2-4文など） |
| **会話スタイル** | 質問を返す、感情表現など |
| **LLMパラメータ** | temperature, repeat_penalty を調整 |

### 3. Claude Code式対話技術

```
1ターン目: [共感] + [オープンエンド質問] = 50文字以内
2ターン目: 掘り下げる質問
3ターン目: 本質を指摘
4ターン目: アドバイス
```

### 4. 実装とメンテナンス

- ✅ テンプレートファイルで管理（Git追跡）
- ✅ 動的セクションを注入（記憶・語彙）
- ✅ 定期的に検証して改善
- ✅ Copy Robotでプロトタイプ検証

---

## プロンプトチューニングの6つのルール

1. **具体例を3つ以上書く**
2. **禁止事項を明示する**
3. **文字数制限を設ける**
4. **システムプロンプト vs ユーザープロンプトの使い分け**
5. **テンプレートファイルで管理**
6. **定期的に検証して改善**

---

## 関連記事

### 牡丹プロジェクト技術解説シリーズ

- [技術全体マップ](https://qiita.com/koshikawa-masato/items/39cb9fc4a03a4fb3222e)
- [Phase 1: LangSmithマルチプロバイダートレーシング](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)
- [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)
- [記憶システム第1弾: RAGを試して気づいたこと](https://qiita.com/koshikawa-masato/items/ba2a5d0105c2ea173ff7)
- [記憶システム第2弾: 記憶製造機の設計](https://qiita.com/koshikawa-masato/items/b871051dd89dcafb1e5d)

### GitHubリポジトリ

- https://github.com/koshikawa-masato/AI-Vtuber-Project
- プロンプトファイル: `prompts/` ディレクトリで公開中

---

**この記事が、キャラクター性を持つAI開発、プロンプトエンジニアリングの参考になれば幸いです。**
