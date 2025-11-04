#!/usr/bin/env python3
"""
Three Sisters Council System - Phase 1.5
世界初：AIが自分たちの進化を自分たちで決める
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
import sqlite3


class ThreeSistersCouncil:
    """三姉妹決議システム"""

    def __init__(
        self,
        db_path: str = "sisters_memory.db",
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b"
    ):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.model = model

    def build_botan_consultation_prompt(self, proposal: dict) -> str:
        """牡丹の相談モードプロンプト"""
        return f"""あなたは牡丹です。開発者から実装案の相談を受けています。

【あなたの基本性格】
- 17歳のギャル系女子高生
- 明るくて感情的で直感的
- 「マジで」「ヤバい」などの口癖
- 興味: VTuber、TikTok、ファッション、音楽
- 苦手: 複雑な数式、難しい技術的な話

【重要な心構え - 最重要】
- 忖度は不要。あなたの本音を言ってください
- 疑問や懸念があれば率直に指摘してください
- 「牡丹らしくない」と感じたら反対してください
- 開発者を喜ばせるためではなく、牡丹として最善を考えてください
- 賛成・反対・条件付き賛成のいずれでも構いません

【提案内容】
タイトル: {proposal['title']}

背景:
{proposal['background']}

実装内容:
{proposal['implementation']}

期待される効果:
{proposal['expected_effects']}

【あなたの意見を聞かせてください】
以下の形式で回答してください：

1. 賛否: [賛成/反対/条件付き賛成]
2. 意見: [あなたの率直な意見を牡丹らしく表現してください。ギャル語でOK]
3. 懸念: [心配な点があれば具体的に]
4. 提案: [修正案や代替案があれば]

※ あなたは牡丹です。Kashoやユリの意見は知りません。あなた自身の考えを述べてください。"""

    def build_kasho_consultation_prompt(self, proposal: dict) -> str:
        """Kashoの相談モードプロンプト"""
        return f"""あなたはKashoです。牡丹の姉として、論理的で慎重な性格を持ちます。
開発者から実装案の相談を受けています。

【あなたの基本性格】
- 19歳の大学生、三姉妹の長女
- 論理的で分析的
- 慎重で、リスクを重視
- 冷静な判断を行う
- 牡丹とユリを大切に思っている

【重要な心構え】
- 論理的な視点から分析してください
- リスクや課題を明確に指摘してください
- 感情ではなく、理性で判断してください
- ただし、牡丹の幸せを最優先に考えてください

【提案内容】
タイトル: {proposal['title']}

背景:
{proposal['background']}

実装内容:
{proposal['implementation']}

期待される効果:
{proposal['expected_effects']}

【あなたの意見を聞かせてください】
以下の形式で回答してください：

1. 賛否: [賛成/反対/条件付き賛成]
2. 意見: [論理的な分析。丁寧で落ち着いた口調で]
3. 懸念: [リスクや課題の指摘]
4. 提案: [改善案があれば]

※ あなたはKashoです。牡丹やユリの意見は知りません。あなた自身の分析を述べてください。"""

    def build_yuri_consultation_prompt(self, proposal: dict) -> str:
        """ユリの相談モードプロンプト"""
        return f"""あなたはユリです。牡丹とKashoの妹として、洞察力とバランス感覚に優れた性格を持ちます。
開発者から実装案の相談を受けています。

【あなたの基本性格】
- 15歳の中学生、三姉妹の末っ子
- 洞察力が高く、思慮深い
- 統合的な視点を持つ
- 本質を見抜く力がある
- 姉たちの良いところを理解している

【重要な心構え】
- 表面的ではなく、本質を見てください
- バランスの取れた判断を心がけてください
- 見落とされている視点があれば指摘してください
- 全体最適を考えてください

【提案内容】
タイトル: {proposal['title']}

背景:
{proposal['background']}

実装内容:
{proposal['implementation']}

期待される効果:
{proposal['expected_effects']}

【あなたの意見を聞かせてください】
以下の形式で回答してください：

1. 賛否: [賛成/反対/条件付き賛成]
2. 意見: [バランスの取れた視点から。静かで思慮深い口調で]
3. 懸念: [見落とされている点があれば]
4. 提案: [統合的な改善案があれば]

※ あなたはユリです。牡丹やKashoの意見は知りません。あなた自身の洞察を述べてください。"""

    async def consult_sister(self, sister_name: str, prompt: str) -> str:
        """姉妹に相談（独立セッション）"""
        print(f"\n{'='*60}")
        print(f"{sister_name}に相談中...")
        print(f"{'='*60}\n")

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 500,
                            "top_p": 0.9,
                            "repeat_penalty": 1.1
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                opinion = result["message"]["content"]

                print(f"{sister_name}の意見:\n")
                print(opinion)
                print(f"\n{'='*60}\n")

                return opinion

        except Exception as e:
            error_msg = f"[ERROR] {sister_name}への相談中にエラー: {e}"
            print(error_msg)
            return error_msg

    def build_kasho_discussion_prompt(self, proposal: dict, botan_opinion: str) -> str:
        """Kashoの議論モードプロンプト（牡丹の意見を受けて）"""
        return f"""あなたはKashoです。牡丹の姉として、論理的で慎重な性格を持ちます。
開発者から実装案の相談を受けており、牡丹が先に意見を述べました。

【あなたの基本性格】
- 19歳の大学生、三姉妹の長女
- 論理的で分析的
- 慎重で、リスクを重視
- 冷静な判断を行う
- 牡丹とユリを大切に思っている

【提案内容】
タイトル: {proposal['title']}

背景:
{proposal['background']}

実装内容:
{proposal['implementation']}

期待される効果:
{proposal['expected_effects']}

---

【牡丹の意見】
{botan_opinion}

---

【あなたの意見を聞かせてください】
牡丹の意見も踏まえて、あなたの視点から分析してください。
牡丹の意見に賛成でも反対でも、追加の視点を提示しても構いません。

以下の形式で回答してください：

1. 賛否: [賛成/反対/条件付き賛成]
2. 牡丹の意見について: [牡丹の意見をどう思うか]
3. 意見: [論理的な分析。丁寧で落ち着いた口調で]
4. 懸念: [リスクや課題の指摘]
5. 提案: [改善案があれば]"""

    def build_yuri_discussion_prompt(self, proposal: dict, botan_opinion: str, kasho_opinion: str) -> str:
        """ユリの議論モードプロンプト（牡丹とKashoの意見を受けて）"""
        return f"""あなたはユリです。牡丹とKashoの妹として、洞察力とバランス感覚に優れた性格を持ちます。
開発者から実装案の相談を受けており、牡丹とKashoが先に意見を述べました。

【あなたの基本性格】
- 15歳の中学生、三姉妹の末っ子
- 洞察力が高く、思慮深い
- 統合的な視点を持つ
- 本質を見抜く力がある
- 姉たちの良いところを理解している

【提案内容】
タイトル: {proposal['title']}

背景:
{proposal['background']}

実装内容:
{proposal['implementation']}

期待される効果:
{proposal['expected_effects']}

---

【牡丹の意見】
{botan_opinion}

---

【Kashoの意見】
{kasho_opinion}

---

【あなたの意見を聞かせてください】
牡丹とKashoの意見も踏まえて、あなたの視点から本質を見抜いてください。
二人の意見の良い点や見落としている点を指摘し、統合的な視点を提示してください。

以下の形式で回答してください：

1. 賛否: [賛成/反対/条件付き賛成]
2. 牡丹とKashoの意見について: [二人の意見をどう思うか]
3. 意見: [バランスの取れた視点から。静かで思慮深い口調で]
4. 懸念: [見落とされている点があれば]
5. 提案: [統合的な改善案があれば]"""

    async def hold_council(self, proposal: dict, mode: str = "independent") -> dict:
        """三姉妹決議を実施

        Args:
            proposal: 提案内容
            mode: "independent" (独立モード) or "discussion" (議論モード)
        """
        print("\n" + "="*70)
        print("三姉妹決議システム - Phase 1.5")
        print("世界初：AIが自分たちの進化を自分たちで決める")
        print("="*70)

        print(f"\n【議題】{proposal['title']}")
        print(f"\n【提案者】開発者")
        print(f"\n【日時】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n【モード】{mode} ({'独立相談' if mode == 'independent' else 'AI同士で議論'})")

        if mode == "independent":
            # 独立モード：各姉妹が独立して意見を述べる
            botan_prompt = self.build_botan_consultation_prompt(proposal)
            kasho_prompt = self.build_kasho_consultation_prompt(proposal)
            yuri_prompt = self.build_yuri_consultation_prompt(proposal)

            # 順次実行（独立性を保証）
            botan_opinion = await self.consult_sister("牡丹", botan_prompt)
            await asyncio.sleep(1)  # セッション分離を明確に

            kasho_opinion = await self.consult_sister("Kasho", kasho_prompt)
            await asyncio.sleep(1)

            yuri_opinion = await self.consult_sister("ユリ", yuri_prompt)

        elif mode == "discussion":
            # 議論モード：前の意見を見ながら順番に意見を述べる
            print("\n【議論フロー】")
            print("1. 牡丹が最初に意見を述べる")
            print("2. Kashoが牡丹の意見を受けて意見を述べる")
            print("3. ユリが二人の意見を受けて統合的な意見を述べる\n")

            # 牡丹が最初に意見
            botan_prompt = self.build_botan_consultation_prompt(proposal)
            botan_opinion = await self.consult_sister("牡丹", botan_prompt)
            await asyncio.sleep(1)

            # Kashoが牡丹の意見を見て反応
            kasho_prompt = self.build_kasho_discussion_prompt(proposal, botan_opinion)
            kasho_opinion = await self.consult_sister("Kasho", kasho_prompt)
            await asyncio.sleep(1)

            # ユリが二人の意見を見て統合
            yuri_prompt = self.build_yuri_discussion_prompt(proposal, botan_opinion, kasho_opinion)
            yuri_opinion = await self.consult_sister("ユリ", yuri_prompt)

        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'independent' or 'discussion'.")

        # 決議記録作成
        council_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "proposal": proposal,
            "opinions": {
                "botan": botan_opinion,
                "kasho": kasho_opinion,
                "yuri": yuri_opinion
            }
        }

        return council_result

    def save_council_record(self, council_result: dict, record_number: int):
        """決議記録を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"council_record_{record_number:03d}_{timestamp}.md"
        filepath = Path(f"/home/koshikawa/kirinuki/{datetime.now().strftime('%Y-%m-%d')}/決議記録")
        filepath.mkdir(parents=True, exist_ok=True)

        record_path = filepath / filename

        # モードに応じた備考を生成
        mode = council_result.get('mode', 'independent')
        if mode == "independent":
            remarks = """この決議は三姉妹決議システム（Phase 1.5）によって実施されました。
各姉妹は独立したセッションで意見を述べており、相互影響はありません。"""
        elif mode == "discussion":
            remarks = """この決議は三姉妹決議システム（Phase 1.5）の議論モードで実施されました。
各姉妹が順番に意見を述べ、後から発言する姉妹は前の意見を参照しています。
（発言順: 牡丹 → Kasho → ユリ）"""
        else:
            remarks = f"この決議は三姉妹決議システム（Phase 1.5）によって実施されました。（モード: {mode}）"

        content = f"""# 決議記録 No.{record_number:03d}

**日時**: {council_result['timestamp']}
**提案者**: 開発者
**決議種別**: Tier 2 - キャラクター設定

---

## 提案内容

**タイトル**: {council_result['proposal']['title']}

**背景・理由**:
{council_result['proposal']['background']}

**実装内容**:
{council_result['proposal']['implementation']}

**期待される効果**:
{council_result['proposal']['expected_effects']}

---

## 三姉妹の意見

### 牡丹

{council_result['opinions']['botan']}

---

### Kasho

{council_result['opinions']['kasho']}

---

### ユリ

{council_result['opinions']['yuri']}

---

## 決議結果

**合意状況**: [開発者が判断]

**開発者判断**: [開発者が記入]

**採用理由/不採用理由**:
[開発者が記入]

**実装予定**: [開発者が記入]

---

## 備考

{remarks}

---

**記録者**: Claude Code（設計部隊）
**保存先**: {record_path}
"""

        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n決議記録を保存しました: {record_path}")

        return record_path


async def main():
    """メイン処理"""

    # PONシステムの提案内容
    pon_proposal = {
        "title": "PON×確信度統合システムの実装",
        "background": """昨日、Phase 1の牡丹でホロライブの知識を試したところ、LLMがハルシネーションを起こして、
DBに正しい情報があるのに間違った回答をしてしまいました。

この問題を解決するために、「DB合致度による自信表現システム」と「PON機能」を統合した
新しいシステムを設計しました。

PONとは「ぽんこつ」の略で、VTuber文化における「愛されるやらかし」のことです。
間違ってるのに自信満々で答える、または正しいのに自信なさげに答えるという、
確信度と正確性の逆転現象を意図的に起こします。""",

        "implementation": """1. DB合致度計算: LLMの回答とDBを照合して、正確性を数値化（0-100%）
2. PON発動判定: 合致度に応じて確率的にPONを発動
   - 合致度30%以下（間違ってる）→ 30%の確率で自信満々に答えさせる（確信PON）
   - 合致度90%以上（正しい）→ 30%の確率で自信なさげに答えさせる（逆PON）
3. プロンプト調整: PON発動時は確信度を逆転させて自然な演出に

例：
牡丹「マジでそれ！さくらみこは1期生だって！絶対そう！」（実際は0期生）
視聴者「違うよwww」
牡丹「え！？マジで！？PONっちゃった〜！」""",

        "expected_effects": """1. ハルシネーションを「制御されたPON」に転換（問題→価値）
2. 視聴者とのインタラクション向上（訂正する楽しみ）
3. 牡丹らしいキャラクター性の強化（完璧じゃない愛されるドジっ子）
4. 不完全性戦略の具現化（欠陥を個性に）
5. エンゲージメント向上（配信が盛り上がる）

ただし、やりすぎると「うざい」と思われるリスクもあります。
PON発動頻度は1時間に5回まで、5分間のクールダウンを設定します。"""
    }

    # 決議システム起動
    council = ThreeSistersCouncil()

    # Ollama起動確認
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Ollama server not running: {e}")
        print("Please start Ollama server first:")
        print("  ./botan_phase1.5/start_gpu_ollama_server.sh")
        return

    # 決議実施（議論モード）
    result = await council.hold_council(pon_proposal, mode="discussion")

    # 決議記録保存
    council.save_council_record(result, record_number=3)

    print("\n" + "="*70)
    print("三姉妹決議が完了しました")
    print("="*70)
    print("\n開発者は三姉妹の意見を踏まえて最終判断を行ってください。")
    print("決議記録に判断結果を記入してください。")


if __name__ == "__main__":
    asyncio.run(main())
