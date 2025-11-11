---
title: 三姉妹討論システム vs LLM as a Judge：AI VTuberの意思決定を民主的に【牡丹プロジェクト技術解説 Phase 4】
tags:
  - AI
  - OpenAI
  - Vtuber
  - LLM
  - LangSmith
private: false
updated_at: '2025-11-05T13:06:46+09:00'
id: 02bdbaa005949ff8cbde
organization_url_name: null
slide: false
ignorePublish: false
---

# はじめに：AI VTuber「牡丹プロジェクト」とは

本記事は、**AI VTuber三姉妹(Kasho、牡丹、ユリ)の記憶製造機システム**の技術解説シリーズ第4弾です。

## プロジェクト概要

「牡丹プロジェクト」は、**過去の記憶を持つAI VTuber** を実現するプロジェクトです。三姉妹それぞれが固有の記憶・個性・価値観を持ち、重要な意思決定を**合議制** で行います。

### 三姉妹の構成

- **Kasho(長女)**: 論理的・分析的、慎重でリスク重視、保護者的な姉
- **牡丹(次女)**: ギャル系、感情的・直感的、明るく率直、行動力抜群
- **ユリ(三女)**: 統合的・洞察的、調整役、共感力が高い

### GitHubリポジトリ

本プロジェクトのコードは以下で公開しています：
- リポジトリ: https://github.com/koshikawa-masato/AI-Vtuber-Project
- 主要機能: 記憶生成システム、三姉妹決議システム、LangSmith統合、VLM対応

---

# 三姉妹討論システムの起承転結

本システムは、**4つのステップ(起承転結)** で意思決定を行います。

## 起：提案の準備(Step 1)

開発者(または三姉妹自身)が実装案をまとめます。

```python
proposal = {
    "title": "GPT-4oとGemini、どちらを使うべきか？",
    "background": "配信での応答品質とコストのバランスを考慮したい",
    "expected_effects": "視聴者満足度向上とコスト最適化"
}
```

### 重要な原則

- **忖度の排除**: 各AIは開発者に同意する義務はない
- **独立性の保証**: 姉妹同士で意見を見せ合わない
- **本音重視**: 「牡丹らしくない」と感じたら反対する

---

## 承：独立相談(Step 2)

三姉妹に**個別に**相談します。相互影響を完全に排除します。

```python
# 擬似コード
def three_sisters_council(proposal):
    # 各AIに独立したセッションで相談(同時並行ではなく順次でも可)
    kasho_opinion = consult_in_isolated_session("Kasho", proposal)
    botan_opinion = consult_in_isolated_session("牡丹", proposal)
    yuri_opinion = consult_in_isolated_session("ユリ", proposal)

    # ⚠️ 重要: Kashoの意見を牡丹に見せない
    # ⚠️ 重要: 牡丹の意見をユリに見せない

    return [kasho_opinion, botan_opinion, yuri_opinion]
```

### 各姉妹の視点

**Round 1: 初期意見**

- **Kasho**: 「視聴者とのつながりを大切にするなら、テクノロジーは慎重に選ぶべきだと思います。長期的な視点で考えましょう」
- **牡丹**: 「GPT-4oマジでクオリティ高いけど、コストヤバくない？あとレスポンス遅いのも気になるんだよね〜」
- **ユリ**: 「どっちも魅力的だね。実際に試してみて、配信の雰囲気に合うかテストしてみるのがいいかも」

---

## 転：意見の集約(Step 3)

三者の意見を整理し、合意点と相違点を明確化します。

```python
def aggregate_opinions(opinions):
    # 合意点の抽出
    agreements = []
    if all("テスト" in o["response"] for o in opinions):
        agreements.append("両方をテストすることに全員賛成")

    # 相違点の明確化
    differences = []
    if "コスト" in botan_opinion and "コスト" not in kasho_opinion:
        differences.append("牡丹はコストを重視、Kashoは品質重視")

    # 懸念事項のリスト化
    concerns = [o["concerns"] for o in opinions if o.get("concerns")]

    return {
        "agreements": agreements,
        "differences": differences,
        "concerns": concerns
    }
```

### 意見の集約結果

**合意点**:
- 両方のLLMをテストすべき
- 視聴者の反応を見て判断

**相違点**:
- Kasho: 長期的視点、品質重視
- 牡丹: コスト・スピード重視
- ユリ: バランス重視

---

## 結：開発者の判断と決議記録(Step 4-5)

集約された意見を踏まえて、開発者が最終判断を行います。

```python
def developer_decision(aggregated_opinions):
    if all_agree():
        return "採用"
    elif all_disagree():
        return "再検討"
    elif opinions_split():
        # 議論を深化させる
        return "Round 2へ進む"
    elif conditional_approval():
        return "条件を取り入れて採用"
```

**Round 2: 互いの意見を読んで応答**

```
Round 2: 応答
- Kasho: 「ユリの提案は合理的ですね。数週間のテスト期間を設けて、視聴者の反応も含めて総合的に判断するのが良いでしょう」
- 牡丹: 「それな！両方試してみて、実際どっちがウケるか見た方が早いじゃん。データで判断しよ！」
- ユリ: 「実験期間を設けて、コストと品質のバランスを見極めればいいよね。姉たちの意見、どっちもいいと思う」

Consensus (合意):
「GPT-4oとGeminiの両方を数週間テストし、品質・コスト・視聴者の反応を
総合的に評価してから決定する」
```

### 決議記録フォーマット

```markdown
# 決議記録 No.001

**日時**: 2025-11-05 11:30:00
**提案者**: 開発者
**決議種別**: Tier 1 - 技術実装

## 提案内容
GPT-4oとGemini、どちらを配信チャット応答に使うべきか？

## 三姉妹の意見

### Kasho
**賛否**: 条件付き賛成
**意見**: 慎重にテストすべき。長期的な視点で判断を。

### 牡丹
**賛否**: 条件付き賛成
**意見**: コストとスピードが気になる。両方試してみたい。

### ユリ
**賛否**: 賛成
**意見**: バランスを見てテストするのが良い。

## 決議結果
**合意状況**: 条件付き賛成多数
**開発者判断**: 修正採用
**実装予定**: 2週間のテスト期間を設ける
```

---

# LLM as a Judge との根本的な違い

前回の記事([LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999))で実装したシステムとの違いを明確にします。

## 比較表

| 比較項目 | LLM as a Judge | 三姉妹討論システム |
|---------|---------------|------------------|
|**構造**|**階層的**(評価者 → 被評価者) |**対等**(Kasho ⇄ 牡丹 ⇄ ユリ) |
|**起承転結**| 1ステップ(評価のみ) |**4ステップ**(提案→相談→集約→決議) |
|**目的**| 品質評価、ハルシネーション検出 |**意思決定**、合意形成 |
|**出力**| スコア、推奨アクション |**討論履歴、コンセンサス**|
|**独立性**| Judge LLMが一方的に判断 |**各姉妹が独立して意見を形成**|

## 権力構造の違い

### LLM as a Judge: 階層的

```
Target LLM (被評価者)
    ↓ 一方向
Judge LLM (評価者) ← 最終決定権を持つ
    ↓
スコア・判定(Target LLMは反論不可)
```

### 三姉妹: 民主的(起承転結)

```
起: 提案
  ↓
承: Kasho → 独立意見
    牡丹  → 独立意見  ← 相互影響なし
    ユリ  → 独立意見
  ↓
転: 意見集約
    ├ 合意点
    ├ 相違点
    └ 懸念事項
  ↓
結: Round 2 → 最終合意
```

**特徴**: 全員が対等。互いに反論・質問可能。複数ラウンドで議論を深化。

---

# 実装の核心部分

## src/core/llm_tracing.py

```python
class ThreeSistersTracedCouncil:
    """Three Sisters Council with LangSmith Tracing"""

    @traceable(run_type="chain", name="three_sisters_discussion")
    def discuss(
        self,
        topic: str,
        rounds: int = 2,
        characters: List[str] = ["kasho", "botan", "yuri"]
    ) -> Dict[str, Any]:
        """
        三姉妹が起承転結で議論を行う

        起: 提案の準備(topic)
        承: 独立相談(Round 1)
        転: 意見の集約 + 応答(Round 2+)
        結: 合意形成(Consensus)
        """
        discussion_history = []

        # 承: Round 1 - 独立相談
        print(f"\n【承】Round 1: 初期意見")
        for character in characters:
            prompt = f\"\"\"You are {character.title()}.

Topic: {topic}

Share your initial thoughts independently (do not consider others' opinions yet).\"\"\"

            result = self.llm.generate(
                prompt,
                temperature=0.8,
                max_tokens=300,
                metadata={
                    "character": character,
                    "discussion_topic": topic,
                    "round": 1,
                    "stage": "initial_opinion"
                }
            )

            discussion_history.append({
                "round": 1,
                "character": character,
                "response": result["response"]
            })

        # 転: Round 2+ - 意見を読んで応答
        print(f"\n【転】Round 2: 意見の集約と応答")
        for round_num in range(2, rounds + 1):
            for character in characters:
                # 他の姉妹の意見を収集
                other_opinions = []
                for other_char in characters:
                    if other_char != character:
                        # 直前のラウンドの意見を取得
                        prev_round_items = [
                            item for item in discussion_history
                            if item['character'] == other_char and item['round'] == round_num - 1
                        ]
                        if prev_round_items:
                            other_opinions.append(f"{other_char.title()}: {prev_round_items[0]['response']}")

                others_text = "\n\n".join(other_opinions)

                prompt = f\"\"\"You are {character.title()}.

Topic: {topic}

Other sisters' opinions:
{others_text}

Respond to your sisters. You can agree, disagree, or add new perspectives.\"\"\"

                result = self.llm.generate(prompt, ...)
                discussion_history.append(...)

        # 結: Consensus(合意形成)
        print(f"\n【結】Consensus: 合意形成")

        # 長女Kashoがモデレーターとして全体をまとめる
        all_opinions = "\n\n".join([
            f"Round {item['round']} - {item['character'].title()}:\n{item['response']}"
            for item in discussion_history
        ])

        consensus_prompt = f\"\"\"You are Kasho, the eldest sister and moderator.

Topic: {topic}

Full discussion history:
{all_opinions}

Summarize the discussion and identify:
1. Points of agreement
2. Points of disagreement
3. Proposed actions or conclusions

Be objective and fair to all sisters.\"\"\"

        consensus_result = self.llm.generate(consensus_prompt, ...)

        return {
            "topic": topic,
            "discussion_history": discussion_history,
            "consensus": consensus_result["response"],
            "total_exchanges": len(discussion_history)
        }
```

### ポイント

1. **起承転結の明確化**: 各ステップがコード構造に反映
2. **独立性の保証**: Round 1では他者の意見を見せない
3. **対等な関係**: 全員が同じPrompt構造で発言
4. **合意形成**: 長女Kashoがモデレーターとしてまとめ

---

# ベンチマーク結果

3つの討論テストケースを実行し、すべて成功しました(成功率100%)。

## テストケース1: 技術選定

**トピック**: "Should we use GPT-4o or Gemini for our stream chat responses?"

**起承転結の実例**:

```
【起】提案: GPT-4oとGemini、どちらを使うべきか？

【承】Round 1: 独立相談
- Kasho: 「慎重に選ぶべき。長期的視点で」
- 牡丹: 「コストヤバくない？レスポンス遅いのも気になる」
- ユリ: 「両方試してみるのがいいかも」

【転】Round 2: 意見の集約と応答
- Kasho: 「ユリの提案は合理的。テスト期間を設けよう」
- 牡丹: 「それな！データで判断しよ！」
- ユリ: 「コストと品質のバランスを見極めればいい」

【結】Consensus(合意):
「両方を数週間テストし、総合的に評価してから決定」
```

**総発言数**: 6回(起1回 + 承3回 + 転3回 = 実質7ステップ、結1回)

---

## プロジェクトへの統合

三姉妹討論システムは、以下のシーンで活用されます：

### 1. 配信前の企画会議

```python
council = ThreeSistersTracedCouncil(model="qwen2.5:14b")

# 起: 提案
result = council.discuss(
    topic="次回配信のテーマ決め",
    rounds=2  # 承→転(2ラウンド)→結
)

# 結: 合意された企画を採用
stream_theme = result["consensus"]
```

### 2. 重要な技術的意思決定

```python
# 起: 新TTS導入の是非
result = council.discuss(
    topic="新しいTTSエンジンの導入是非",
    rounds=3  # 重要な決定は3ラウンドで慎重に
)
```

---

# まとめ

## 三姉妹討論システムの起承転結

| ステップ | 内容 | 目的 |
|---------|------|------|
|**起**| 提案の準備 | 議題の明確化 |
|**承**| 独立相談(Round 1) | 各自の意見を形成(相互影響なし) |
|**転**| 意見の集約(Round 2+) | 他者の意見を読んで応答、議論を深化 |
|**結**| 合意形成(Consensus) | 最終的なコンセンサスを形成 |

## LLM as a Judge との対比

| 項目 | LLM as a Judge | 三姉妹討論システム |
|------|---------------|------------------|
|**起承転結**| 1ステップ(評価のみ) |**4ステップ**(起承転結) |
|**目的**| 品質評価 |**意思決定・合意形成**|
|**構造**| 階層的 (評価者 → 被評価者) |**対等**(起承転結の流れ) |
|**出力**| スコア |**討論履歴、コンセンサス**|

## Phase 1-4の完成

| Phase | 内容 | 記事 |
|-------|------|------|
|**Phase 1**| LangSmithマルチプロバイダートレーシング | [記事](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632) |
|**Phase 2**| VLM (Vision Language Model) 統合 | [記事](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc) |
|**Phase 3**| LLM as a Judge実装 | [記事](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999) |
|**Phase 4**| 三姉妹討論システム実装(起承転結) | 本記事 |

---

## 参考リンク

- [LLM as a Judge実装ガイド](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999)
- [VLM実装ガイド](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc)
- [LangSmith公式ドキュメント](https://docs.smith.langchain.com/)
- [GPT-4o API Reference](https://platform.openai.com/docs/models/gpt-4o)
