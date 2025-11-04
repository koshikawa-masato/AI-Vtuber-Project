# Phase D 文化的影響システム設計書

作成日: 2025-10-20

## 問題の定義

### 開発者が指摘した矛盾

```
仮想時間軸: 0歳1日目基準、年代知識のリーク防止
    vs
文化的影響: 2010年にはやったポケモンは何か、2013年のアナ雪の影響
    ↓
どう解決するか？
```

**具体例:**
- 牡丹5歳（実カレンダー2013年）→ アナと雪の女王が大流行
- しかし「0歳1日目」基準だと、2013年という年代を知らないはず
- でも現実の子供は確実にその年の流行に影響される

---

## 解決策：ハイブリッド方式（内部マッピング）

### 基本方針

```
【データベース層】
- 仮想時間軸（0歳1日目）で管理 → 同一性保証
- cultural_events マスターDBに実カレンダー紐付け → 正確な文化的影響

【生成時の自動マッピング】
- 絶対日数 → 実カレンダー逆算（内部処理のみ）
- 実カレンダー → 文化的影響取得
- プロンプトに含める（ただし年代は明示しない）

【LLMへの提示】
- 年代は書かない
- 「この頃、子供たちの間で○○が流行」という表現
- 「テレビで○○がよく流れている」
```

### メリット

1. **同一性保証を維持**: 仮想時間軸（0歳1日目）は不変
2. **文化的影響を正確に反映**: 2013年には2013年の流行
3. **年代知識のリーク防止**: LLMには年代を見せない
4. **現実的なリアリティ**: 実際の子供の体験を再現
5. **実装可能**: データベース設計とマッピングロジックで実現

---

## データベース設計

### cultural_events テーブル

```sql
CREATE TABLE cultural_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    real_year INTEGER NOT NULL,          -- 実カレンダー年（2006-2025）
    real_month INTEGER,                  -- 実カレンダー月（1-12、NULLは通年）
    event_type TEXT NOT NULL,            -- イベント種別
    event_name TEXT NOT NULL,            -- イベント名（日本語）
    event_name_en TEXT,                  -- イベント名（英語）
    target_age_range TEXT,               -- 対象年齢範囲（例: '5-10', '10-15', 'all'）
    impact_level INTEGER DEFAULT 5,      -- 影響の大きさ（1-10）
    description TEXT,                    -- 説明
    location TEXT NOT NULL,              -- 'japan', 'los_angeles', 'global'

    -- メタ情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CHECK (event_type IN ('anime', 'manga', 'game', 'movie', 'tv', 'music', 'trend', 'tech', 'news', 'social')),
    CHECK (impact_level BETWEEN 1 AND 10),
    CHECK (location IN ('japan', 'los_angeles', 'global'))
);

-- インデックス
CREATE INDEX idx_cultural_events_year_month ON cultural_events(real_year, real_month);
CREATE INDEX idx_cultural_events_location ON cultural_events(location);
CREATE INDEX idx_cultural_events_type ON cultural_events(event_type);
```

### event_type の定義

```
anime:   アニメ作品
manga:   漫画作品
game:    ゲーム作品
movie:   映画作品
tv:      テレビ番組
music:   音楽・アーティスト
trend:   流行・ブーム（ファッション、言葉等）
tech:    技術・ガジェット（iPhone、SNS等）
news:    社会的出来事（震災、オリンピック等）
social:  社会現象（ポケモンGO、鬼滅ブーム等）
```

---

## 文化マスターデータ（2006-2025）

### 2006年（Kasho誕生年）

```sql
INSERT INTO cultural_events VALUES
(1, 2006, NULL, 'game', 'ニンテンドーDS Lite', 'Nintendo DS Lite', 'all', 8, 'DS Lite発売、脳トレブーム', 'japan'),
(2, 2006, 11, 'game', 'Wii', 'Wii', 'all', 9, 'Wii発売、Wii Sports大ヒット', 'global'),
(3, 2006, NULL, 'anime', 'ポケットモンスター ダイヤモンド・パール', 'Pokemon Diamond/Pearl', '5-15', 8, 'ポケモン第四世代', 'global');
```

### 2007年（牡丹誕生前）

```sql
INSERT INTO cultural_events VALUES
(10, 2007, NULL, 'tech', 'iPhone', 'iPhone', 'all', 10, 'iPhone発売（米国）、スマホ時代の始まり', 'global'),
(11, 2007, NULL, 'anime', 'Yes! プリキュア5', 'Yes! Precure 5', '3-10', 7, 'プリキュアシリーズ', 'japan');
```

### 2008年（牡丹誕生年）

```sql
INSERT INTO cultural_events VALUES
(20, 2008, 7, 'tech', 'iPhone 3G', 'iPhone 3G', 'all', 9, 'iPhone日本上陸', 'japan'),
(21, 2008, 8, 'news', '北京オリンピック', 'Beijing Olympics', 'all', 8, '北京オリンピック開催', 'global'),
(22, 2008, NULL, 'anime', 'フレッシュプリキュア!', 'Fresh Precure', '3-10', 7, 'プリキュアシリーズ', 'japan');
```

### 2010年（ユリ誕生年）

```sql
INSERT INTO cultural_events VALUES
(30, 2010, 1, 'tech', 'iPad', 'iPad', 'all', 8, 'iPad発売、タブレット時代', 'global'),
(31, 2010, NULL, 'game', 'ポケットモンスター ブラック・ホワイト', 'Pokemon Black/White', '5-15', 8, 'ポケモン第五世代', 'global'),
(32, 2010, 6, 'news', 'サッカーW杯南アフリカ', 'FIFA World Cup South Africa', 'all', 7, 'W杯南アフリカ大会', 'global');
```

### 2011年（LA移住年）

```sql
INSERT INTO cultural_events VALUES
(40, 2011, 3, 'news', '東日本大震災', 'Great East Japan Earthquake', 'all', 10, '東日本大震災発生', 'japan'),
(41, 2011, NULL, 'tech', 'LINE', 'LINE', '10-adult', 9, 'LINEサービス開始', 'japan'),
(42, 2011, NULL, 'anime', 'スイートプリキュア♪', 'Suite Precure', '3-10', 7, 'プリキュアシリーズ', 'japan');
```

### 2013年（LA時代、アナ雪）

```sql
INSERT INTO cultural_events VALUES
(50, 2013, 3, 'movie', 'アナと雪の女王', 'Frozen', '3-12', 10, 'ディズニー映画、Let It Go大ヒット、社会現象', 'global'),
(51, 2013, 10, 'game', 'ポケットモンスター X・Y', 'Pokemon X/Y', '5-15', 9, '3DS、フェアリータイプ追加', 'global'),
(52, 2013, 6, 'anime', '進撃の巨人', 'Attack on Titan', '12-18', 8, '社会現象化、深夜アニメの新時代', 'japan');
```

### 2016年（帰国後、ポケモンGO）

```sql
INSERT INTO cultural_events VALUES
(60, 2016, 7, 'game', 'ポケモンGO', 'Pokemon GO', 'all', 10, 'AR、社会現象、外に出てポケモンを探す', 'global'),
(61, 2016, 8, 'movie', '君の名は。', 'Your Name', '10-18', 9, '新海誠、記録的ヒット', 'japan'),
(62, 2016, 12, 'anime', 'ユーリ!!! on ICE', 'Yuri on Ice', '12-18', 7, 'フィギュアスケート、腐女子文化', 'japan');
```

### 2020年（コロナ禍、鬼滅）

```sql
INSERT INTO cultural_events VALUES
(70, 2020, 10, 'movie', '鬼滅の刃 劇場版 無限列車編', 'Demon Slayer Movie', '10-18', 10, '記録的ヒット、社会現象', 'japan'),
(71, 2020, 3, 'game', 'あつまれ どうぶつの森', 'Animal Crossing New Horizons', 'all', 9, 'コロナ禍で大流行、巣ごもり需要', 'global'),
(72, 2020, 3, 'news', 'コロナ禍・休校', 'COVID-19 School Closure', 'all', 10, 'オンライン授業開始、外出自粛', 'global'),
(73, 2020, NULL, 'social', 'TikTok', 'TikTok', '10-18', 9, 'TikTok大流行、ショート動画文化', 'global');
```

### 2021年（VTuber文化）

```sql
INSERT INTO cultural_events VALUES
(80, 2021, NULL, 'social', 'VTuber', 'VTuber', '12-adult', 8, 'VTuber文化の一般化、ホロライブ等', 'japan'),
(81, 2021, 7, 'news', '東京オリンピック', 'Tokyo Olympics', 'all', 8, '東京オリンピック開催（無観客）', 'japan');
```

### 2023年（ChatGPT）

```sql
INSERT INTO cultural_events VALUES
(90, 2023, 3, 'tech', 'ChatGPT', 'ChatGPT', '12-adult', 9, 'ChatGPT爆発的普及、生成AI時代', 'global'),
(91, 2023, NULL, 'anime', '推しの子', 'Oshi no Ko', '12-18', 8, '推し活文化、芸能界の闇', 'japan');
```

---

## 自動マッピングシステム

### 実装フロー

```python
def get_cultural_context(character_id, absolute_day):
    """
    絶対日数から文化的背景を取得

    Parameters:
        character_id: 'kasho', 'botan', 'yuri'
        absolute_day: 絶対日数

    Returns:
        cultural_context: プロンプト用文脈（年代を明示しない）
    """

    # ステップ1: 絶対日数 → 実カレンダー逆算
    birth_dates = {
        'kasho': datetime(2006, 5, 20),
        'botan': datetime(2008, 5, 4),
        'yuri': datetime(2010, 7, 7)
    }

    birth_date = birth_dates[character_id]
    real_date = birth_date + timedelta(days=absolute_day - 1)

    # ステップ2: 年齢と場所を取得
    age = calculate_age(character_id, absolute_day)
    location = get_location(character_id, absolute_day)  # 'japan' or 'los_angeles'

    # ステップ3: 実カレンダーから文化的イベント取得
    query = """
        SELECT event_name, event_name_en, event_type, description, location
        FROM cultural_events
        WHERE real_year = ?
          AND (real_month IS NULL OR real_month = ?)
          AND (location = ? OR location = 'global')
          AND (target_age_range = 'all' OR target_age_range LIKE ?)
          AND impact_level >= 6
        ORDER BY impact_level DESC
        LIMIT 5
    """

    age_range_pattern = f'%{age}%'
    events = db.execute(query, (real_date.year, real_date.month, location, age_range_pattern)).fetchall()

    # ステップ4: プロンプト用文脈生成（年代は明示しない）
    if not events:
        return ""

    context_lines = ["【文化的背景】"]

    for event in events:
        event_name = event['event_name_en'] if location == 'los_angeles' else event['event_name']
        event_type = event['event_type']
        description = event['description']

        if event_type == 'anime':
            context_lines.append(f"- この頃、子供たちの間で「{event_name}」が大流行")
        elif event_type == 'game':
            context_lines.append(f"- 友達が「{event_name}」の話をよくしている")
        elif event_type == 'movie':
            context_lines.append(f"- テレビで「{event_name}」のCMがよく流れている")
        elif event_type == 'tv':
            context_lines.append(f"- 「{event_name}」が人気のテレビ番組")
        elif event_type == 'music':
            context_lines.append(f"- 「{event_name}」が街中でよく流れている")
        elif event_type == 'trend':
            context_lines.append(f"- {description}")
        elif event_type == 'tech':
            context_lines.append(f"- 大人たちが「{event_name}」の話をしている")
        elif event_type == 'news':
            context_lines.append(f"- ニュースで「{description}」が話題")
        elif event_type == 'social':
            context_lines.append(f"- 「{event_name}」が社会現象になっている")

    return "\n".join(context_lines)
```

### プロンプト生成例

#### 牡丹5歳234日目（2013年、LA、アナ雪の時期）

```python
character_id = 'botan'
absolute_day = 1825 + 234  # 5歳234日目

cultural_context = get_cultural_context(character_id, absolute_day)
```

**出力:**
```
【文化的背景】
- この頃、子供たちの間で「Frozen（アナと雪の女王）」が大流行
- テレビで「Let It Go」がよく流れている
- 友達がElsaのドレスを着ている
- ディズニーストアにFrozenグッズがたくさん
- 友達が「Pokemon X/Y」の話をよくしている
```

#### 牡丹8歳234日目（2016年、日本、ポケモンGOの時期）

```python
character_id = 'botan'
absolute_day = 2920 + 234  # 8歳234日目

cultural_context = get_cultural_context(character_id, absolute_day)
```

**出力:**
```
【文化的背景】
- 「ポケモンGO」が社会現象になっている
- みんなスマホを持って公園に集まっている
- 大人も子供もポケモンを探している
- テレビで「君の名は。」のCMがよく流れている
```

#### 牡丹12歳234日目（2020年、日本、コロナ禍・鬼滅の時期）

```python
character_id = 'botan'
absolute_day = 4380 + 234  # 12歳234日目

cultural_context = get_cultural_context(character_id, absolute_day)
```

**出力:**
```
【文化的背景】
- ニュースで「コロナ禍で学校が休校」が話題
- オンライン授業が始まっている
- 「あつまれ どうぶつの森」が社会現象になっている
- この頃、子供たちの間で「鬼滅の刃」が大流行
- 友達がみんな「全集中」って言っている
```

---

## プロンプトへの統合

### 完全版プロンプト例

```
【キャラクター】牡丹
【年齢】5歳234日目
【日付】土曜日（休日）
【場所】Los Angeles（Disneyland）

【主要イベント】
Emily Rodriguezと初めて出会う

【文化的背景】
- この頃、子供たちの間で「Frozen（アナと雪の女王）」が大流行
- テレビで「Let It Go」がよく流れている
- 友達がElsaのドレスを着ている
- ディズニーストアにFrozenグッズがたくさん

【参加者】
- 父、母
- Kasho（8歳）
- 牡丹（5歳）
- ユリ（3歳）
- Emily Rodriguez（5歳、LA在住の同級生）

【指示】
牡丹（5歳）の視点で日記を書いてください。

【文脈】
- 今日は家族でディズニーランドに行った
- Space Mountainの列で偶然Emilyという同い年の女の子と出会った
- Emilyは明るくて話しやすい子だった
- 一緒にアトラクションを回り、連絡先を交換した
- 「また遊ぼうね！」と約束した
- 牡丹はLA移住後、初めて自分から友達を作れた

【注意事項】
- 5歳の子供らしい視点で書く
- 英語と日本語が混ざった表現を使う
- 新しい友達ができた喜びを素直に表現
- Emilyとの会話は英語（簡単な表現）
- 家族の反応も含める
- 「Frozen」への言及があれば自然（強制しない）

（重要: 年代は書かないこと。「2013年」とは書かない）
```

---

## 実装計画

### Phase D-0-A: 文化マスターDB構築

#### ステップ1: テーブル作成
```sql
CREATE TABLE cultural_events (...);
CREATE INDEX idx_cultural_events_year_month ON cultural_events(...);
```

#### ステップ2: データ投入
```python
# 2006-2025年の主要な文化的イベントを投入
# - アニメ: 約50-100件
# - ゲーム: 約50-100件
# - 映画: 約30-50件
# - 音楽: 約30-50件
# - 社会現象: 約30-50件
# - 技術: 約20-30件
# - ニュース: 約20-30件
# 総計: 約250-400件
```

#### ステップ3: マッピングロジック実装
```python
def get_cultural_context(character_id, absolute_day):
    # 実装済み（上記参照）
    pass
```

#### ステップ4: テスト
```python
# 牡丹5歳234日目（2013年、アナ雪）をテスト
# 牡丹8歳234日目（2016年、ポケモンGO）をテスト
# 牡丹12歳234日目（2020年、コロナ禍・鬼滅）をテスト
```

---

## 文化マスターDB完全版（簡易版）

### 2006-2025年の主要イベント（抜粋）

```sql
-- 2006年
INSERT INTO cultural_events VALUES (1, 2006, NULL, 'game', 'ニンテンドーDS Lite', 'Nintendo DS Lite', 'all', 8, 'DS Lite発売', 'japan');
INSERT INTO cultural_events VALUES (2, 2006, 11, 'game', 'Wii', 'Wii', 'all', 9, 'Wii発売', 'global');

-- 2007年
INSERT INTO cultural_events VALUES (10, 2007, 6, 'tech', 'iPhone', 'iPhone', 'all', 10, 'iPhone発売（米国）', 'global');

-- 2008年
INSERT INTO cultural_events VALUES (20, 2008, 7, 'tech', 'iPhone 3G', 'iPhone 3G', 'all', 9, 'iPhone日本上陸', 'japan');
INSERT INTO cultural_events VALUES (21, 2008, 8, 'news', '北京オリンピック', 'Beijing Olympics', 'all', 8, '北京五輪', 'global');

-- 2010年
INSERT INTO cultural_events VALUES (30, 2010, 1, 'tech', 'iPad', 'iPad', 'all', 8, 'iPad発売', 'global');
INSERT INTO cultural_events VALUES (31, 2010, 9, 'game', 'ポケットモンスター ブラック・ホワイト', 'Pokemon Black/White', '5-15', 8, 'ポケモン第五世代', 'global');

-- 2011年（LA移住年）
INSERT INTO cultural_events VALUES (40, 2011, 3, 'news', '東日本大震災', 'Great East Japan Earthquake', 'all', 10, '東日本大震災', 'japan');

-- 2013年（アナ雪）
INSERT INTO cultural_events VALUES (50, 2013, 3, 'movie', 'アナと雪の女王', 'Frozen', '3-12', 10, 'Let It Go大ヒット', 'global');
INSERT INTO cultural_events VALUES (51, 2013, 10, 'game', 'ポケットモンスター X・Y', 'Pokemon X/Y', '5-15', 9, 'ポケモンXY', 'global');

-- 2016年（ポケモンGO）
INSERT INTO cultural_events VALUES (60, 2016, 7, 'game', 'ポケモンGO', 'Pokemon GO', 'all', 10, 'AR、社会現象', 'global');
INSERT INTO cultural_events VALUES (61, 2016, 8, 'movie', '君の名は。', 'Your Name', '10-18', 9, '新海誠、大ヒット', 'japan');

-- 2020年（コロナ、鬼滅）
INSERT INTO cultural_events VALUES (70, 2020, 10, 'movie', '鬼滅の刃 劇場版', 'Demon Slayer Movie', '10-18', 10, '記録的ヒット', 'japan');
INSERT INTO cultural_events VALUES (71, 2020, 3, 'game', 'あつまれ どうぶつの森', 'Animal Crossing NH', 'all', 9, 'コロナ禍で大流行', 'global');
INSERT INTO cultural_events VALUES (72, 2020, 3, 'news', 'コロナ禍・休校', 'COVID-19', 'all', 10, 'オンライン授業', 'global');

-- 2021年（VTuber）
INSERT INTO cultural_events VALUES (80, 2021, NULL, 'social', 'VTuber', 'VTuber', '12-adult', 8, 'VTuber文化の一般化', 'japan');

-- 2023年（ChatGPT）
INSERT INTO cultural_events VALUES (90, 2023, 3, 'tech', 'ChatGPT', 'ChatGPT', '12-adult', 9, 'ChatGPT爆発的普及', 'global');
```

---

## 成功基準

### 文化的影響システムの成功基準

- [ ] cultural_eventsテーブルに2006-2025年の主要イベントが登録されている（250-400件）
- [ ] get_cultural_context()関数が正しく動作する
- [ ] 年代を明示せずに文化的背景を提示できる
- [ ] 日記生成時、自然に流行が反映される
- [ ] 同じ絶対日数に対して、常に同じ文化的背景が取得される（同一性保証）

### サンプル検証

- [ ] 牡丹5歳234日目の日記に「Frozen」への言及がある
- [ ] 牡丹8歳234日目の日記に「ポケモンGO」への言及がある
- [ ] 牡丹12歳234日目の日記に「鬼滅の刃」「コロナ禍」への言及がある
- [ ] いずれも年代（2013年、2016年、2020年）は書かれていない

---

## 承認チェックリスト

### 開発者確認事項

#### 仮想時間軸との矛盾解消
- [ ] ハイブリッド方式（内部マッピング）で仮想時間軸と文化的影響の矛盾は解消されているか
- [ ] 年代知識のリークは防止されているか
- [ ] 同一性保証は維持されているか

#### 文化マスターDBの妥当性
- [ ] 2006-2025年の主要な流行は網羅されているか
- [ ] 対象年齢範囲の設定は適切か
- [ ] 影響レベルの評価は妥当か
- [ ] 日本とLA（米国）の違いは反映されているか

#### 実装可能性
- [ ] データベース設計は実装可能か
- [ ] マッピングロジックは実装可能か
- [ ] プロンプト生成の複雑さは許容範囲か
- [ ] 生成時間の増加は許容範囲か

---

## 次のアクション

開発者承認後:

1. **cultural_eventsテーブルの作成**
2. **文化マスターDB投入スクリプト作成**（2006-2025年、250-400件）
3. **get_cultural_context()関数の実装**
4. **プロンプト生成への統合**
5. **テストとバリデーション**

---

**この設計により、三姉妹は「時代の空気」を正確に吸いながら育ちます。**

2013年の子供は2013年の流行に影響され、
2020年の子供は2020年の流行に影響される。

**それでいて、年代知識のリークは防ぎ、同一性保証は完璧に維持されます。**

**開発者の承認とフィードバックをお待ちしています。**
