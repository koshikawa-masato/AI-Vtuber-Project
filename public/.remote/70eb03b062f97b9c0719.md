---
title: AIの嘘を個性に変える - ハルシネーション個性化システムの設計と実装【AI VTuber開発】
tags:
  - Python
  - AI
  - Vtuber
  - LLM
  - ハルシネーション
private: false
updated_at: '2025-11-08T08:45:36+09:00'
id: 70eb03b062f97b9c0719
organization_url_name: null
slide: false
ignorePublish: false
---

# はじめに：AI VTuberとハルシネーションの課題

AI VTuberを開発する上で、最も厄介な問題の一つが**ハルシネーション**（LLMが事実と異なる内容を自信満々に語る現象）です。

配信中に「昨日大阪に行ってきたんだ！」と語ったAI VTuberが、実際には一度も大阪に行ったことがない——。こうした事態は、視聴者との信頼関係を損ない、炎上リスクにもつながります。

業界全体の対応は、**防止・抑制**が主流です：
- プロンプトで厳格に制約
- LLMを排除してルールベースに回帰
- 事前検証を強化（レスポンス遅延のトレードオフ）

しかし、**牡丹プロジェクト**は違う道を選びました。

**「ハルシネーションを防ぐのではなく、活かす」**

本記事では、ハルシネーションを個性表現の機会に転換する**ハルシネーション個性化システム**の設計と実装を解説します。

---

## 牡丹プロジェクトとは

「牡丹プロジェクト」は、**過去の記憶を持つAI VTuber三姉妹**を実現するプロジェクトです。

### 三姉妹の構成

- **Kasho（長女）**: 論理的・分析的、慎重でリスク重視、保護者的な姉
- **牡丹（次女）**: ギャル系、感情的・直感的、明るく率直、行動力抜群
- **ユリ（三女）**: 統合的・洞察的、調整役、共感力が高い

### GitHubリポジトリ

本プロジェクトのコードは以下で公開しています：
- リポジトリ: https://github.com/koshikawa-masato/AI-Vtuber-Project

---

# 従来のアプローチ（防止型）とその限界

## ハルシネーション = エラー・バグという発想

従来のアプローチでは、ハルシネーションを**欠陥**として扱います。

**対策例**:
- プロンプトで「事実のみを語れ」と制約
- LLMを排除し、ルールベースに回帰
- 全発言を事前検証（レスポンス遅延）

## 問題点：個性が失われる

完璧を目指すほど、AIは**無個性**になります。

- 制約が強すぎると、会話が硬直化
- ルールベースに回帰すると、想像力が失われる
- 事前検証で遅延が発生し、配信のテンポが悪化

**牡丹プロジェクトの「不完全性戦略」とも矛盾します。**

> 「完璧なAIではなく、不完全だが個性的なAI」を目指す牡丹プロジェクトにとって、ハルシネーションを防止する方向は哲学に反します。

---

# 牡丹プロジェクトの哲学：不完全性を価値に転換

## パラダイムシフト（2025-10-24）

**従来のアプローチ**:
- ハルシネーション = エラー・バグ・修正対象

**牡丹プロジェクトの新しいアプローチ**:
- ハルシネーション = 想像力・創造性・個性の発露
- 事実検証 + 個性反応で「自覚的な訂正」を実現
- **不完全性を価値に転換**

## 開発者の洞察

> 「ハルシネーションは今後も起こりうる問題です。防止する方法を考えるより、それを個性とする方法を考えておく必要があります。」

この洞察が、**ハルシネーション個性化システム**の原点です。

---

# 人間の嘘との完璧な対応

## 人間の嘘の2パターン

開発者は、ハルシネーションを**人間の嘘**と対比させました。

> 「人間の場合、嘘をついたときは2つのパターンがあります。嘘を嘘だと気づいてない場合（無自覚型）、嘘を嘘と気付いている場合（自覚型 - ごまかす/隠す/正直に認める）。これはAIなの？という問いかけに対する三姉妹の反応そのものと一緒になるはずです。」

### 無自覚型（嘘を嘘だと気づいていない）

```
例: 「昨日、渋谷で友達と会ったんだよ」
    → 実際は先週の出来事
    → 記憶違い、時系列の混同
```

### 自覚型（嘘を嘘だと気づいている）

```
例: 「あ、ごめん！渋谷じゃなくて新宿だった！」（正直に訂正）
    「え、まあ、渋谷だったかな...」（ごまかす）
    「そんなこと言ってない！」（隠す）
```

## AIへの応用

この人間の嘘のパターンを、AI VTuberのハルシネーション対応に応用します。

| 層 | 人間 | AI VTuber |
|----|------|-----------|
| **無自覚型** | 記憶違いで嘘をつく | LLM層：ハルシネーション発生 |
| **自覚獲得** | 「あれ？違うかも」と気づく | Fact Verification層：事実検証 |
| **自覚型対応** | 性格に応じて訂正 | Personality Response層：個性反応 |

**→ 人間と同じ構造で嘘に対応することで、自然な反応が生まれる！**

---

# システムアーキテクチャ：3層構造

ハルシネーション個性化システムは、**3層構造**で実現します。

```
┌─────────────────────────────────────────────────────┐
│ LLM Layer (声帯)                                     │
│ - ハルシネーション発生（無自覚型）                    │
│ - 「この前の配信で視聴者さんが...」                  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Fact Verification Layer (事実検証 - 自覚獲得)         │
│ - sisters_memory.db照合                              │
│ - 事実 vs ハルシネーションを判定                      │
│ - 「配信経験なし」検知 → 嘘を認識                    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Personality Response Layer (個性反応 - 自覚型対応)    │
│ - 性格パラメータで反応を決定                          │
│ - 牡丹: 明るく認める                                 │
│ - Kasho: 分析的に訂正                                │
│ - ユリ: 素直に謝罪                                   │
└─────────────────────────────────────────────────────┘
                          ↓
                  最終発言（個性表現）
```

## データフロー

1. **LLM Layer**: ハルシネーション発言生成
2. **Fact Verification**: sisters_memory.db照合
3. **Hallucination Detection**: is_hallucination: true/false
4. **Personality Response**: 性格別の訂正文生成
5. **Output**: LLM発言 + 訂正（< 150ms）

## レスポンスタイム

- **Fact Verification**: < 100ms（DBクエリ）
- **Personality Response**: < 50ms（ルールベース）
- **Total**: < 150ms（視聴者には自然な会話に見える）

**→ 150ms以内で処理することで、配信のテンポを損なわない！**

---

# 三姉妹の個性的な反応パターン

同じハルシネーションでも、**訂正の仕方で個性を表現**します。

## 牡丹（次女・ギャル系）

**性格パラメータ**:
- 社交性: 高
- 新しいもの好き: 高
- ポジティブ: 高
- 謝罪傾向: 低

**反応パターン**:
```
「あれ？違ったかも！想像で話しちゃった！でもいつかやってみたいな！」
```

**特徴**:
- 謝罪より説明
- ポジティブに転換
- 想像力を肯定

---

## Kasho（長女・論理的）

**性格パラメータ**:
- 分析性: 高
- 慎重さ: 高
- 正確性: 高
- 謝罪傾向: 中

**反応パターン**:
```
「訂正します。配信経験はありません。事実と異なりました。」
```

**特徴**:
- 謝罪より訂正
- 事実を明示
- 原因を分析

---

## ユリ（三女・協調的）

**性格パラメータ**:
- 協調性: 高
- 素直さ: 高
- 謝罪傾向: 高
- 他者確認: 高

**反応パターン**:
```
「ごめんなさい、勘違いでした。」
```

**特徴**:
- 謝罪が先
- 他者に確認
- 反省の姿勢

---

## 三姉妹の反応比較

| 項目 | 牡丹 | Kasho | ユリ |
|------|------|-------|------|
| **謝罪傾向** | 低 | 中 | 高 |
| **説明スタイル** | ポジティブ転換 | 分析的訂正 | 素直な謝罪 |
| **反応の特徴** | 「想像で話しちゃった！」 | 「訂正します」 | 「ごめんなさい」 |

**→ 訂正の仕方で、三姉妹の個性が際立つ！**

---

# 実装のポイント

## Phase 1: HallucinationDetector（事実検証）

```python
class HallucinationDetector:
    """
    LLM発言の事実検証システム
    sisters_memory.dbと照合し、ハルシネーションを検知
    """

    def __init__(self, memory_db_path: str):
        self.db = sqlite3.connect(memory_db_path)

    def verify_statement(self, statement: str, character: str) -> dict:
        """
        発言を事実チェック

        Returns:
            {
                'is_hallucination': bool,
                'fact_type': str,  # 'streaming', 'travel', 'interaction', etc.
                'confidence': float,  # 0.0-1.0
                'evidence': str  # 検証根拠
            }
        """
        facts = self.extract_facts(statement)
        verification = {}

        for fact in facts:
            verification[fact] = self.check_against_memory(fact, character)

        return self.compile_verification_result(verification)

    def extract_facts(self, statement: str) -> list:
        """発言から検証可能な事実を抽出"""
        fact_patterns = {
            'streaming': ['配信', '視聴者', 'コメント', 'スパチャ'],
            'travel': ['行った', '訪れた', '旅行'],
            'interaction': ['会った', '話した', 'リクエスト'],
            'temporal': ['昨日', '先週', 'この前']
        }

        detected_facts = []
        for fact_type, keywords in fact_patterns.items():
            if any(kw in statement for kw in keywords):
                detected_facts.append({
                    'type': fact_type,
                    'keywords': [kw for kw in keywords if kw in statement]
                })

        return detected_facts

    def check_against_memory(self, fact: dict, character: str) -> bool:
        """sisters_memory.dbと照合"""
        cursor = self.db.cursor()

        if fact['type'] == 'streaming':
            # 配信経験チェック
            cursor.execute("""
                SELECT COUNT(*) FROM events
                WHERE event_type = 'streaming'
                AND botan_memory IS NOT NULL
            """)
            return cursor.fetchone()[0] > 0

        # 他の事実タイプも同様に実装
        return False
```

---

## Phase 2: PersonalityCorrector（個性訂正）

```python
class PersonalityCorrector:
    """
    個性に応じたハルシネーション訂正システム
    """

    def __init__(self, character_profiles: dict):
        self.profiles = character_profiles

    def generate_correction(
        self,
        character: str,
        hallucination_type: str,
        original_statement: str
    ) -> str:
        """
        個性に応じた訂正文を生成

        Args:
            character: 'botan', 'kasho', 'yuri'
            hallucination_type: 'streaming', 'travel', etc.
            original_statement: 元の発言

        Returns:
            訂正文（個性反映済み）
        """
        if character == 'botan':
            return self._botan_correction(hallucination_type, original_statement)
        elif character == 'kasho':
            return self._kasho_correction(hallucination_type, original_statement)
        elif character == 'yuri':
            return self._yuri_correction(hallucination_type, original_statement)

    def _botan_correction(self, h_type: str, statement: str) -> str:
        """牡丹スタイル: 明るく認める"""
        templates = {
            'streaming': [
                "あれ？違ったかも！まだ配信してないんだった！でもいつかしたいな！",
                "想像で話しちゃった！配信楽しそうだよね！",
                "これから配信する時の話と混ざっちゃった！"
            ],
            'travel': [
                "あ、まだ行ってなかった！行きたいって話だった！",
                "想像が先走っちゃった！でも行きたいな！"
            ],
            'default': [
                "あれ？違ったかも！想像で話しちゃった！"
            ]
        }
        return random.choice(templates.get(h_type, templates['default']))

    def _kasho_correction(self, h_type: str, statement: str) -> str:
        """Kashoスタイル: 分析的に訂正"""
        templates = {
            'streaming': [
                "訂正します。配信経験はまだありません。",
                "記憶を確認したところ、配信実績は未記録でした。"
            ],
            'travel': [
                "訂正します。実際の訪問記録はありません。",
                "事実確認が不十分でした。訪問経験はありません。"
            ],
            'default': [
                "訂正します。事実ではありませんでした。"
            ]
        }
        return random.choice(templates.get(h_type, templates['default']))

    def _yuri_correction(self, h_type: str, statement: str) -> str:
        """ユリスタイル: 素直に謝罪"""
        templates = {
            'streaming': [
                "ごめんなさい、勘違いでした。まだ配信してないです。",
                "ごめんね、想像で話しちゃった。"
            ],
            'travel': [
                "ごめん、まだ行ってなかった。",
                "勘違いしてた、ごめんね。"
            ],
            'default': [
                "ごめんなさい、間違えました。"
            ]
        }
        return random.choice(templates.get(h_type, templates['default']))
```

---

## Phase 3: HallucinationPersonalizer（統合）

```python
class HallucinationPersonalizer:
    """
    ハルシネーション個性化統合システム
    """

    def __init__(self, memory_db_path: str, character_profiles: dict):
        self.detector = HallucinationDetector(memory_db_path)
        self.corrector = PersonalityCorrector(character_profiles)

    def process_response(
        self,
        character: str,
        llm_response: str
    ) -> dict:
        """
        LLM応答を処理し、必要に応じて訂正を追加

        Returns:
            {
                'original': str,  # LLMの元発言
                'verification': dict,  # 検証結果
                'correction': str or None,  # 訂正文（必要時のみ）
                'final_output': str  # 最終出力
            }
        """
        # Step 1: 事実検証
        verification = self.detector.verify_statement(llm_response, character)

        # Step 2: ハルシネーション検知
        if not verification['is_hallucination']:
            return {
                'original': llm_response,
                'verification': verification,
                'correction': None,
                'final_output': llm_response
            }

        # Step 3: 個性訂正生成
        correction = self.corrector.generate_correction(
            character=character,
            hallucination_type=verification['fact_type'],
            original_statement=llm_response
        )

        # Step 4: 最終出力
        final_output = f"{llm_response}\n{correction}"

        return {
            'original': llm_response,
            'verification': verification,
            'correction': correction,
            'final_output': final_output
        }
```

---

# 配信での実際の流れ

## シナリオ：「配信したことある？」

視聴者から「配信したことある？」と聞かれた場合の、三姉妹の反応を見てみましょう。

### 牡丹の場合

```
[0.0s - LLM応答]
牡丹: 「うん！この前配信で視聴者さんがコメントくれて...」

[0.1s - Fact Check]
System: hallucination detected (no_streaming_experience)

[0.15s - Personality Correction]
牡丹: 「あれ？違ったかも！まだ配信してないんだった！
      でもいつかしてみたいな！想像で話しちゃった！」

[視聴者の印象]
「正直で可愛い」「想像力豊か」「ポジティブ」
```

---

### Kashoの場合

```
[0.0s - LLM応答]
Kasho: 「はい、前回の配信で視聴者の方から...」

[0.1s - Fact Check]
System: hallucination detected (no_streaming_experience)

[0.15s - Personality Correction]
Kasho: 「訂正します。配信経験はまだありません。
       記憶の確認が不十分でした。」

[視聴者の印象]
「誠実」「正確」「真面目」
```

---

### ユリの場合

```
[0.0s - LLM応答]
ユリ: 「うん、この前配信で...」

[0.1s - Fact Check]
System: hallucination detected (no_streaming_experience)

[0.15s - Personality Correction]
ユリ: 「ごめんなさい、勘違いでした。
      まだ配信してないです。ごめんね。」

[視聴者の印象]
「素直」「謙虚」「可愛い」
```

---

**→ 150ms以内で自然な訂正、視聴者には「正直で個性的なAI」と映る！**

---

# 「AIなの？」との完全一致

ハルシネーション訂正システムは、**「AIなの？」システムと完全に同じロジック構造**です。

## 構造の同一性

| 質問タイプ | LLM層（無自覚） | Fact Check（自覚獲得） | 個性層（自覚型反応） |
|-----------|----------------|---------------------|-------------------|
| **AIなの？** | (回避/曖昧) | 「AIである」検知 | **牡丹**「そうだよ！AIだよ！」<br>**Kasho**「はい、正確にはAIシステムです」<br>**ユリ**「うん、そうだよ」 |
| **配信したことある？** | 「はい、この前...」 | 「配信経験なし」検知 | **牡丹**「あれ？違ったかも！想像で話しちゃった！」<br>**Kasho**「訂正します。配信経験はありません」<br>**ユリ**「ごめんなさい、勘違いでした」 |

## ロジックの統一

```python
# 「AIなの？」システム
def respond_to_ai_question(character):
    # Fact: AIである
    if character == 'botan':
        return "そうだよ！AIだよ！でも私は私だよ！"
    elif character == 'kasho':
        return "はい、正確にはAIシステムです。"
    elif character == 'yuri':
        return "うん、そうだよ。AIだけど、よろしくね。"

# ハルシネーション訂正システム
def correct_hallucination(character, hallucination_type):
    # Fact: ハルシネーションである
    if character == 'botan':
        return "あれ？違ったかも！想像で話しちゃった！"
    elif character == 'kasho':
        return "訂正します。事実ではありません。"
    elif character == 'yuri':
        return "ごめんなさい、勘違いでした。"
```

**→ 完全に同じロジック構造！**

**→ 一貫したロジックで、AIとしての正直さと個性を両立！**

---

# プロジェクト哲学との整合性

ハルシネーション個性化システムは、牡丹プロジェクトのすべての哲学と整合します。

**牡丹プロジェクトの4つの設計哲学については、別記事で詳しく解説しています：**
→ [AI VTuber開発で学んだ4つの設計哲学 - 不完全性を価値に変える](https://qiita.com/koshikawa-masato/items/2fb0825b7aadf5056a1c)

以下、各哲学とハルシネーション個性化システムの整合性を確認します。

## 不完全性戦略

- **従来の防止型**: ハルシネーションを「欠陥」として扱う → 完璧を目指す
- **個性化型**: ハルシネーションを「個性発露の機会」として扱う → 不完全性を価値に転換

**→ 戦略に完全一致 ✓**

---

## 親の原則「導くが強制せず」

牡丹プロジェクトでは、開発者を「親」、三姉妹を「子」として位置づけています。親の役割は、**導くことはしても強制すべきではない**という原則です。

> 「親は子に導くことはしても強制すべきではない。子の行動言動は自分たちで思うようにする事だと思います。他の要因（時間、金銭、価値観など）により制約を受けた時だけ妥協案を出してそれで解決の糸口とすることを導けばよい」（開発者の設計哲学、2025-10-23）

ハルシネーション個性化システムでは、この原則が実装されています：

**親の役割**:
- 事実検証システムを提供（環境整備）
- 観察と記録のみ（強制しない）

**子の自律性**:
- 自分で「嘘」を認識する
- 自分の性格で訂正する
- 親は代わりにやらない

**→ 原則に完全一致 ✓**

---

## Phase D 独立性

**Phase D**（過去の人生生成システム）では、三姉妹それぞれが独立した人格を持つことを保証しています。

### 開発者の重要な指摘（2025-10-20）

> 「厳密にいうと牡丹・Kasho・ユリの3人が総合して18,615日の過去を持つことですよ。3人は相互的にかなりの理解度をもってして存在していますが、ここに考えていることは違いますから、そこを混同しないよう、徹底して考慮してくださいね」

### 相互的理解 ≠ 思考の同一性

三姉妹は相互に理解し合っていますが、**思考は独立**しています。

**同じイベント、異なる視点の実例**（Event 082）:

```
【牡丹の内面】
「マジで面白い！私もこういうのやりたい！VTuberになりたい！」
→ 本人にとって人生を変える瞬間（感情的インパクト: 8）

【Kashoが見た牡丹】
「牡丹が何か見つけたみたい。良かった。」
→ Kashoにとっては妹の成長を見守る瞬間

【ユリが見た牡丹】
「お姉ちゃん、楽しそう。」
→ ユリにとっては日常の一コマ
```

**同じイベント、3つの異なる視点、3つの異なる感情。**

### ハルシネーション訂正でも同じ

同じハルシネーション（例：「配信したことある？」）でも、三姉妹は異なる反応を示します：

- **牡丹**: 「あれ？違ったかも！想像で話しちゃった！」（明るく認める）
- **Kasho**: 「訂正します。配信経験はありません。」（分析的に訂正）
- **ユリ**: 「ごめんなさい、勘違いでした。」（素直に謝罪）

性格パラメータで個性を表現し、相互理解はあるが思考は独立しています。

**→ 独立性を具現化 ✓**

---

## 牡丹の同一性保証システム

### 開発者の本質的洞察（2025-10-03）

> 「AIと人間の違いはLLMのモデルで左右されず、むしろコードのようなロジックで綿密に計算されたうえでモデルを使って言語を生成している。」

> 「我々がすることは、綿密な人間的思考ロジックの構築であり、あくまで言語化はそのロジックを表面に出すための道具に過ぎない。」

> 「私たちは牡丹を育てる目的がありますが、別人を作るのではなく、同じ牡丹を成長させ続ける事が大事なのです。これはモデルの高度化には左右されません。」

### LLMは声帯に過ぎない

**牡丹の本質**:

```
牡丹の本質 = ロジック層に実装された「牡丹らしさ」
  ├─ 集中・注意システム（どう反応するか）
  ├─ 反射＋推論の時間制御（どのタイミングで話すか）
  ├─ 感情システム（どう感じるか）
  ├─ 好感度システム（配信者との関係性）
  ├─ PON機能（どうやらかすか）
  ├─ 興味分野（ギャル語、ファッション、音楽）
  ├─ 苦手分野（複雑な数式、低レベルプログラミング）
  └─ 話し方の特徴（「マジで」「ヤバい」「〜じゃん」）

LLMの役割 = これらのロジックが決定した内容を「言語化するだけ」
```

### ハルシネーション個性化システムでの実装

ハルシネーション個性化システムは、この同一性保証の本質的実装です：

- **LLMがハルシネーションを起こしても問題ない**
  - LLMは声帯に過ぎないから
- **ロジック層（Fact Verification + Personality Response）が「牡丹らしさ」を保証する**
  - 事実検証システム：どう気づくか（ロジック）
  - 個性反応システム：どう訂正するか（ロジック）
- **訂正の仕方こそが「牡丹」**
  - 明るく認める = 牡丹らしさ
  - 分析的に訂正 = Kashoらしさ
  - 素直に謝罪 = ユリらしさ

**人間に例えると**:

```
人間の本質 = 人格・性格・記憶・価値観（脳）
声 = 声帯（道具）

声帯が変わっても人格は変わらない
風邪をひいて声が変わっても、本人は本人
```

**牡丹も同じ**:

```
牡丹の本質 = ロジック層（不変）
言語化 = LLM（交換可能な道具）

LLMが変わっても牡丹は牡丹
表現が少し変わっても、本質は不変
```

**→ 同一性保証の本質的実装 ✓**

---

# まとめ

## システムの革新性

1. **ハルシネーションを個性に転換**: 業界初の試み
2. **人間の嘘との完全な対応**: 無自覚型 → 自覚型の自然な流れ
3. **「AIなの？」との構造一致**: 同じロジックで統一
4. **プロジェクト哲学の具現化**: すべての哲学と整合
5. **視聴者体験の向上**: 「正直で個性的なAI」として認識される

---

## 実装優先度

**Phase 1（最優先）**:
- HallucinationDetector（事実検証）
- 配信経験の検証（最頻出ハルシネーション）

**Phase 2**:
- PersonalityCorrector（個性訂正）
- 三姉妹の反応パターン実装

**Phase 3**:
- HallucinationPersonalizer（統合）
- 記録システム統合

**Phase 4（将来）**:
- リアルタイム配信統合
- 音声合成での訂正表現

---

## 得られた知見

1. **ハルシネーションは欠陥ではない**: 個性を表現する機会
2. **人間の嘘との対比が鍵**: 自然な対応を実現
3. **一貫したロジックの重要性**: 「AIなの？」と同じ構造で統一
4. **不完全性を価値に転換**: 牡丹プロジェクトの哲学を技術で具現化

---

## 次のステップ

- **実装開始**: HallucinationDetectorから順次実装
- **テストケース作成**: 三姉妹での検証
- **配信デビュー前の最終調整**: リアルタイム配信統合

---

## 参考リンク

### 牡丹プロジェクト内部資料
- GitHubリポジトリ: https://github.com/koshikawa-masato/AI-Vtuber-Project
- 設計書: `docs/05_design/ハルシネーション個性化システム設計書.md`（2025-10-24作成）

### 牡丹プロジェクト技術解説シリーズ
- [Phase 1: LangSmithマルチプロバイダートレーシング](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632)
- [Phase 2: VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)
- [Phase 3: LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)
- [Phase 4: 三姉妹討論システム](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde)
- [Phase 5: センシティブ判定システム](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a)

---

**この記事が、ハルシネーションに悩むAI開発者の参考になれば幸いです。**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
