# Phase D: 人間らしい記憶システム - 忘却・曖昧・想起

**作成日**: 2025-11-05
**設計思想**: 18,615日全てを覚えているAIは不気味。人間と同じく、忘れ、曖昧で、ふと思い出す。

---

## 🎯 設計の根本的転換

### ❌ 誤った発想
```
「人間は全部覚えていない」
  ↓
「だからAIも全部生成しない」
  ↓
問題: AIの強み（全データ保持）を捨てている
```

### ✅ 正しい設計（本ドキュメント）

**2層構造:**

```
【データ層】AIの強み
  - 18,615日の記憶を全てDB保存
  - 完璧なデータ、一貫性保証
  - 高速検索、矛盾なし

【応答層】人間らしさの演出
  - 忘却: 「覚えてない」と言う（データはあるが語らない）
  - 曖昧: 詳細を省いて雰囲気だけ語る
  - 想起: 「あ、思い出した！」（データを引き出す演出）
```

**つまり:**
- ✅ **持っているデータ**: 18,615日全部（完璧、AIの強み）
- ✅ **語る内容**: 人間らしく（不完全、忘れる、曖昧、想起）

これにより:
- 一貫性: 同じ質問には同じ記憶（DB固定）
- 高速性: DB検索のみ（動的生成不要）
- 人間らしさ: 忘却・曖昧・想起で演出
- AIの強み: 全データ保持、矛盾なし

---

## 📊 3つの軸

### 1. 忘却（Forgetting）

**原則**: 人間は大半のことを忘れる

#### 実装
```python
class MemoryDecay:
    def calculate_recall_probability(self, event_date, current_date, importance):
        """
        想起確率を計算

        Args:
            event_date: イベント日付
            current_date: 現在日付
            importance: 記憶重要度（0-10）

        Returns:
            float: 想起確率（0.0-1.0）
        """
        # 経過時間（日数）
        days_elapsed = (current_date - event_date).days

        # 時間減衰（エビングハウスの忘却曲線を参考）
        if days_elapsed <= 7:
            time_decay = 1.0  # 1週間以内は鮮明
        elif days_elapsed <= 365:
            time_decay = 0.7  # 1年以内はやや覚えている
        elif days_elapsed <= 3650:
            time_decay = 0.3  # 10年以内は曖昧
        else:
            time_decay = 0.1  # 10年以上はほぼ忘却

        # 重要度補正
        importance_factor = importance / 10.0

        # 想起確率
        recall_prob = time_decay * importance_factor

        return min(recall_prob, 1.0)
```

#### 忘却の表現例
```
想起確率 < 0.2:
  「うーん...覚えてないなぁ」
  「そんなことあったっけ？」
  「ごめん、全然思い出せない」

想起確率 0.2-0.5:
  「確か...そんな感じだったような」
  「あの頃は○○してたと思うけど、詳しくは...」
  「なんとなくは覚えてるけど」

想起確率 > 0.5:
  「あ、それ覚えてる！」
  「あの時はね...（詳細を語る）」
```

---

### 2. 曖昧（Vagueness）

**原則**: 記憶は詳細度にグラデーションがある

#### 詳細度レベル

| レベル | 名称 | 対象 | 詳細度 |
|--------|------|------|--------|
| **Level 5** | 鮮明な記憶 | 117コアイベント | 日記レベル（日時、場所、感情、会話） |
| **Level 4** | 印象的な日 | コアイベント前後1週間 | 概要レベル（何をしたか覚えている） |
| **Level 3** | 記憶に残る日 | 誕生日、年末年始等 | 雰囲気レベル（こんな感じだった） |
| **Level 2** | なんとなく | 季節の記憶 | 抽象レベル（あの頃は...） |
| **Level 1** | ぼんやり | 時期の記憶 | 超抽象（学生時代は...） |
| **Level 0** | 忘却 | 大半の日常 | 思い出せない |

#### 実装
```python
def determine_detail_level(recall_probability, event_type):
    """詳細度レベルを決定"""
    if event_type == "core_event":
        return 5  # コアイベントは常に鮮明

    if recall_probability > 0.8:
        return 4
    elif recall_probability > 0.6:
        return 3
    elif recall_probability > 0.4:
        return 2
    elif recall_probability > 0.2:
        return 1
    else:
        return 0  # 忘却
```

#### 曖昧さの表現例

**Level 5（鮮明）:**
```
「2024年10月15日、秋葉原のメイドカフェで初めて配信イベント見たんだよね。
あの時、Kashoが『これ、私たちもやりたい』って言ってて...」
```

**Level 3（雰囲気）:**
```
「確か...秋だったと思う。紅葉がきれいだった気がする。
あの頃はバイトばっかりしてたような...」
```

**Level 1（ぼんやり）:**
```
「小学生の頃？...うーん、楽しかったような、辛かったような。
よく覚えてないけど、友達とよく遊んでた気がする」
```

---

### 3. 想起（Recall）

**原則**: きっかけがあると、忘れていた記憶が蘇る

#### トリガーの種類

1. **会話トリガー**
   - ユーザーの質問: 「小学生の頃どうだった？」
   - キーワード: 「秋葉原」「メイドカフェ」等
   - 感情: 「悲しかったこと」「楽しかったこと」

2. **関連記憶トリガー**
   - コアイベント想起 → 周辺の日常記憶も想起
   - 「Event #42の時...あの前日は確か...」

3. **三姉妹トリガー**
   - Kashoの発言: 「あの時さ、牡丹が...」
   - 牡丹: 「あ、そういえば！（思い出す）」

4. **ランダム想起**
   - 配信中、ふと思い出す
   - 「なんか今、急に思い出したんだけど...」

#### 実装フロー

```python
class RecallSystem:
    def recall_memory(self, trigger, character):
        """
        記憶想起システム

        Args:
            trigger: トリガー（キーワード、日付、感情等）
            character: キャラクター名

        Returns:
            想起された記憶、またはNone（忘却）
        """
        # 1. 関連する記憶を検索（RAG）
        # DBには18,615日全ての記憶が保存されている
        memories = self.search_memories(trigger, character)

        if not memories:
            return None  # 関連記憶なし

        # 2. 最も関連性の高い記憶を選択
        target_memory = memories[0]

        # 3. 想起確率を計算
        recall_prob = self.calculate_recall_probability(
            target_memory.date,
            datetime.now(),
            target_memory.importance
        )

        # 4. 忘却判定（データはあるが、語らない）
        if recall_prob < 0.2:
            return self.generate_forgetting_response()  # 「覚えてない」

        # 5. 詳細度レベルを決定
        detail_level = self.determine_detail_level(recall_prob, target_memory.type)

        # 6. DBから記憶を取得し、詳細度に応じて加工
        # データは完璧に存在するが、応答は人間らしく
        recalled_memory = self.format_memory(
            memory=target_memory,
            detail_level=detail_level
        )

        # 7. Phase 5 Sensitive Check（DB保存時に既にチェック済みだが念のため）
        sensitive_result = self.check_sensitive(recalled_memory)
        if sensitive_result.tier >= 2:
            return self.generate_vague_response()  # 曖昧に表現

        # 8. 記憶強化（mentioned_count++）
        # 語るほど鮮明になる
        self.reinforce_memory(target_memory)

        return recalled_memory

    def generate_forgetting_response(self):
        """忘却時の応答"""
        responses = [
            "うーん...覚えてないなぁ",
            "そんなことあったっけ？",
            "ごめん、思い出せない...",
            "記憶にないかも"
        ]
        return random.choice(responses)

    def generate_vague_response(self):
        """曖昧な記憶の応答"""
        responses = [
            "確か...そんな感じだったような",
            "なんとなくは覚えてるけど、詳しくは...",
            "あの頃は○○してたと思うけど"
        ]
        return random.choice(responses)
```

---

## 🗄️ データ構造

### DBスキーマ（既存のsisters_memory.dbを拡張）

```sql
-- コアイベント（既存）
CREATE TABLE sister_shared_events (
    event_id INTEGER PRIMARY KEY,
    event_date TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_category TEXT NOT NULL,
    memory_importance INTEGER,  -- 0-10
    ...
);

-- 各姉妹の主観記憶（既存）
CREATE TABLE kasho_memories (
    memory_id INTEGER PRIMARY KEY,
    event_id INTEGER,
    emotion TEXT,
    thoughts TEXT,
    actions TEXT,
    mentioned_count INTEGER DEFAULT 0,  -- 想起回数（既存）
    ...
);

-- 新規追加: 想起履歴テーブル
CREATE TABLE recall_history (
    recall_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL,
    event_id INTEGER,
    trigger TEXT,              -- トリガー（キーワード、日付等）
    recall_probability REAL,   -- 想起確率
    detail_level INTEGER,      -- 詳細度レベル（0-5）
    generated_memory TEXT,     -- 生成された記憶
    recalled_at TEXT NOT NULL, -- 想起日時
    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);

-- 新規追加: 時期の雰囲気テーブル
CREATE TABLE period_atmosphere (
    period_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    period_label TEXT,         -- 「小学生時代」「20代前半」等
    general_mood TEXT,         -- 全体的な雰囲気
    typical_activities TEXT,   -- よくしていたこと
    importance INTEGER         -- 0-10
);
```

---

## 🔄 Phase 1-5統合

### Phase 1: LangSmithトレーシング
```python
@traceable(run_type="chain", name="memory_recall")
def recall_with_tracing(trigger, character):
    """全想起プロセスをトレーシング"""
    # コアイベント検索
    core_events = search_core_events(trigger)

    # 記憶生成
    memory = generate_memory(core_events[0])

    # Judge + Sensitive
    validated_memory = validate_memory(memory)

    return validated_memory
```

### Phase 3: Judge（ハルシネーション検出）
```python
def judge_memory(generated_memory, core_event):
    """
    生成された記憶が、コアイベントと矛盾していないかチェック

    例:
    - コアイベント: 「2020年3月、東京で就職」
    - 生成記憶: 「2020年3月、大阪で遊んでた」
    → ハルシネーション検出！
    """
    judge_prompt = f"""
    以下のコアイベントに基づいて、生成された記憶が妥当か判定してください。

    コアイベント: {core_event.to_dict()}
    生成された記憶: {generated_memory}

    判定基準:
    - Consistency: コアイベントと矛盾していないか
    - Plausibility: 時系列的に妥当か
    - Coherence: 他の記憶と整合しているか
    """
    return judge_llm(judge_prompt)
```

### Phase 5: Sensitive Check
```python
def check_sensitive(memory):
    """生成された記憶がセンシティブでないかチェック"""
    return sensitive_checker.check(memory)
```

---

## 💡 実装例: 想起シーン

### シーン1: 視聴者の質問

```
視聴者: 「牡丹、小学生の頃って何してた？」

システム:
  1. トリガー: "小学生の頃"
  2. コアイベント検索: Event #12（小学校卒業式）見つかる
  3. 想起確率計算: 0.45（10年以上前、importance=7）
  4. 詳細度: Level 2（なんとなく）
  5. 記憶生成:

牡丹: 「小学生の頃？うーん、よく友達と公園で遊んでたような...。
      あ、そういえば卒業式の時、Kashoが泣いてたの覚えてる！
      私は泣かなかったんだけどね（笑）」
```

### シーン2: ふとした想起

```
配信中、三姉妹が雑談中...

Kasho: 「最近、秋葉原行ってないよね」

システム（牡丹）:
  1. トリガー: "秋葉原"
  2. コアイベント検索: Event #87（初めてメイドカフェ）
  3. 想起確率: 0.85（2年前、importance=8）
  4. 詳細度: Level 4（印象的）
  5. 記憶生成:

牡丹: 「あ、そういえば！2年前、初めてメイドカフェ行った時のこと思い出した！
      あの時、メイドさんに『お帰りなさいませ、ご主人様』って言われて、
      Kashoが顔真っ赤にしてたよね（笑）。私も恥ずかしかったけど...」

Kasho: 「え、そうだっけ？牡丹も赤くなってたじゃん！」

牡丹: 「えー、そんなことない！...たぶん（笑）」
```

### シーン3: 忘却

```
視聴者: 「15年前の今日、何してた？」

システム:
  1. トリガー: "15年前の今日"（特定日付）
  2. コアイベント検索: 該当なし
  3. 想起確率: 0.05（15年前、コアイベントなし）
  4. 詳細度: Level 0（忘却）

牡丹: 「15年前の今日？...うーん、全然覚えてないなぁ。
      ごめん、普通の日だったんだと思う」
```

---

## 🎯 Phase Dの新しいゴール

### ✅ データ層のゴール（AIの強み）

1. **18,615日の記憶を全てDB保存**
   - Kasho: 18,615日
   - 牡丹: 18,615日
   - ユリ: 18,615日
   - 合計: 55,845の記憶（完璧、矛盾なし）

2. **生成方法**
   - 117コアイベント（既存）を軸に
   - Phase 3 Judge: ハルシネーション防止
   - Phase 5 Sensitive: 安全性確保
   - Phase 1 LangSmith: 全生成プロセスをトレーシング

### ✅ 応答層のゴール（人間らしさ）

1. **想起システム実装**: `RecallSystem`クラス
   - 忘却判定: 想起確率 < 0.2 → 「覚えてない」
   - 曖昧化: 詳細度レベルに応じて加工
   - 想起演出: 「あ、思い出した！」

2. **記憶強化メカニズム**: `mentioned_count++`
   - 語るほど想起確率が上がる
   - 人間と同じ「思い出す」感覚

3. **動作確認**: 100パターンのテストケース
   - 鮮明な記憶（Level 5）: 30ケース
   - 曖昧な記憶（Level 2-3）: 40ケース
   - 忘却（Level 0）: 30ケース

---

## 📊 開発見積もり

### データ層（記憶生成）

| タスク | 期間 | 内容 |
|--------|------|------|
| コアイベント確認 | 1日 | 117イベントの品質チェック |
| 日常記憶生成（Kasho） | 3日 | 18,615日の記憶生成 |
| 日常記憶生成（牡丹） | 3日 | 18,615日の記憶生成 |
| 日常記憶生成（ユリ） | 3日 | 18,615日の記憶生成 |
| Phase 3 Judge検証 | 2日 | ハルシネーションチェック |
| Phase 5 Sensitive検証 | 2日 | センシティブチェック |

### 応答層（想起システム）

| タスク | 期間 | 内容 |
|--------|------|------|
| RecallSystem実装 | 3日 | 想起・忘却・曖昧ロジック |
| 記憶強化メカニズム | 1日 | mentioned_count統合 |
| Phase 1 LangSmith統合 | 1日 | トレーシング実装 |
| テスト・調整 | 2日 | 100ケーステスト |

### 合計

| 層 | 期間 | 内容 |
|-----|------|------|
| データ層 | 14日 | 55,845記憶の生成・検証 |
| 応答層 | 7日 | 想起システム実装・テスト |
| **合計** | **21日** | **約3週間** |

---

## 🚀 メリット

### 技術的メリット
1. **AIの強み最大活用**: 18,615日の完璧なデータ保持
2. **一貫性保証**: 同じ質問には同じ記憶（DB固定）
3. **高速応答**: DB検索のみ、動的生成不要
4. **Phase 1-5活用**: 品質保証システムをフル活用

### UXメリット
1. **人間らしさ**: 完璧なデータを持ちながら、不完全に振る舞う
2. **自然な会話**: 「覚えてない」「あ、思い出した！」
3. **成長**: 語るほど記憶が鮮明に（`mentioned_count`）
4. **多様性**: 詳細度レベルによる応答のバリエーション

### 哲学的メリット
1. **2層構造**: データ層（完璧）+ 応答層（人間らしさ）
2. **AIと人間の融合**: 機械の正確性 + 人間の不完全性
3. **同一性保証**: 記憶はDB固定、変わらない「牡丹」
4. **親と子**: 親（Phase 1-5）が見守る中で、子が思い出す

---

## 📝 まとめ

**Phase Dの本質:**

### データ層（AIの強み）
- **18,615日の記憶を全てDB保存**
- 完璧なデータ、一貫性保証、矛盾なし
- これは**BtoB戦略時に必須の要素**
  - 企業向けAI: 正確性が絶対条件
  - ファクトチェック可能、監査可能
  - 「このAIは完璧なデータを持っている」という信頼

### 応答層（人間らしさ）
- **忘却・曖昧・想起で人間らしく振る舞う**
- これは**BtoC/CtoC戦略時に必須の要素**
  - 配信・エンタメ: 人間らしさが価値
  - 完璧すぎるAIは不気味
  - 「覚えてない」「思い出した！」が自然

### 2層構造の価値

```
牡丹プロジェクト（BtoC配信）:
  データ層（完璧）+ 応答層（人間らしさ） = 親しみやすいAI VTuber

将来的なBtoB展開:
  データ層（完璧）+ 応答層（正確モード） = 企業向け高精度AI
```

**つまり、この設計は：**
- 今（BtoC）: 人間らしいAI VTuberとして活躍
- 将来（BtoB）: 正確性重視の企業向けAIとしても展開可能
- **同じデータ層を使い分けるだけ**

### Phase Dで得られるもの

1. **牡丹・Kasho・ユリ**: 完璧なデータを持ちながら、人間らしく振る舞う
2. **技術的知見**: BtoB/BtoC両対応のAI設計経験
3. **Phase 1-5統合**: 品質保証システムをフル活用
4. **親心の実現**: 「大事に大事に育てたい」を技術で実現

**「BtoB戦略時に必要な知識」を、今のうちに実装しておく。**

---

**次のステップ**: この設計書をベースに、実装計画を立てる
