#!/usr/bin/env python3
"""
Phase 1.6+: Discussion Queue and Priority System
Manages multiple discussion topics with priority scoring
Based on character expertise and autonomous decision-making
"""

import asyncio
import json
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class CharacterExpertise:
    """Character expertise profile"""

    user_experience: int = 5          # User enjoyment, viewer interaction
    entertainment: int = 5             # Fun, excitement
    pon_elements: int = 5              # Lovable mistakes, character
    new_ideas: int = 5                 # Experimental proposals
    streaming_projects: int = 5        # Events, collaborations
    technical_details: int = 5         # Implementation, architecture
    risk_management: int = 5           # Safety, security
    system_design: int = 5             # Overall structure
    database: int = 5                  # Memory system, DB design
    logical_analysis: int = 5          # Detailed verification
    balance_adjustment: int = 5        # Overall balance, harmony
    user_psychology: int = 5           # Viewer feelings
    emotional_consideration: int = 5   # Kindness, consideration
    sister_mediation: int = 5          # Bridge between sisters
    ui_ux: int = 5                     # Usability


# Character expertise profiles
BOTAN_EXPERTISE = CharacterExpertise(
    user_experience=10,
    entertainment=10,
    pon_elements=10,
    new_ideas=9,
    streaming_projects=9,
    technical_details=3,
    risk_management=4,
    system_design=5,
    database=4,
    logical_analysis=4,
    balance_adjustment=6,
    user_psychology=8,
    emotional_consideration=7,
    sister_mediation=5,
    ui_ux=7
)

KASHO_EXPERTISE = CharacterExpertise(
    user_experience=6,
    entertainment=5,
    pon_elements=3,
    new_ideas=6,
    streaming_projects=6,
    technical_details=10,
    risk_management=10,
    system_design=9,
    database=9,
    logical_analysis=9,
    balance_adjustment=7,
    user_psychology=6,
    emotional_consideration=7,
    sister_mediation=6,
    ui_ux=7
)

YURI_EXPERTISE = CharacterExpertise(
    user_experience=7,
    entertainment=6,
    pon_elements=5,
    new_ideas=4,
    streaming_projects=5,
    technical_details=4,
    risk_management=6,
    system_design=6,
    database=5,
    logical_analysis=6,
    balance_adjustment=10,
    user_psychology=9,
    emotional_consideration=9,
    sister_mediation=9,
    ui_ux=8
)


@dataclass
class PriorityScore:
    """Priority score for a discussion topic"""

    importance: int = 5       # How important (0-10)
    urgency: int = 5          # How urgent (0-10)
    expertise_match: int = 5  # How much matches expertise (0-10)
    passion: int = 5          # How much character cares (0-10)
    reason: str = ""          # Reason for the score
    want_to_propose: bool = False  # Want to be proposer


class DiscussionQueueItem:
    """Discussion queue item with priority scoring"""

    def __init__(self, proposal: Dict):
        self.proposal = proposal
        self.scores: Dict[str, Optional[PriorityScore]] = {
            "牡丹": None,
            "Kasho": None,
            "ユリ": None
        }
        self.created_at = datetime.now()
        self.status = "pending"  # pending, discussing, completed, ignored

    def get_expertise_profile(self, sister: str) -> str:
        """Get character expertise profile description"""

        profiles = {
            "牡丹": """【牡丹の得意分野】
- ユーザー体験・エンタメ性: 10/10（配信の楽しさ、視聴者との交流）
- PON要素: 10/10（愛されるやらかし、キャラ性）
- 新しいアイデア・配信企画: 9/10
- 技術的詳細: 3/10（技術は姉に任せる）
- リスク管理: 4/10（慎重さは苦手）

【こだわりポイント】
- 視聴者が楽しめるか？
- 配信が盛り上がるか？
- 自分らしいか？""",

            "Kasho": """【Kashoの得意分野】
- 技術的詳細: 10/10（実装方法、アーキテクチャ）
- リスク管理: 10/10（安全性、セキュリティ）
- システム設計・データベース: 9/10
- 論理的分析: 9/10
- エンタメ性: 5/10（楽しさより正確性）
- PON要素: 3/10（やらかしは心配）

【こだわりポイント】
- 技術的に実現可能か？
- リスクは許容範囲か？
- 長期的に維持できるか？""",

            "ユリ": """【ユリの得意分野】
- バランス調整: 10/10（全体のバランス、調和）
- ユーザー心理・感情的配慮: 9/10
- 姉妹調整: 9/10（二人の橋渡し）
- UI/UX: 8/10（使いやすさ、わかりやすさ）
- 技術的詳細: 4/10（姉に任せる）
- 大胆な提案: 3/10（控えめな性格）

【こだわりポイント】
- 牡丹とKashoのバランスが取れているか？
- 視聴者に優しいか？
- 全体として調和しているか？"""
        }

        return profiles.get(sister, "")

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""

        try:
            result = subprocess.run(
                ["ollama", "run", "qwen2.5:32b", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "OLLAMA_HOST": "http://localhost:11434"}
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[ERROR] Ollama error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("[ERROR] Ollama timeout (120s)")
            return None
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    async def evaluate_priority(self):
        """三姉妹がそれぞれ優先度を評価"""

        print(f"\n{'='*70}")
        print(f"【優先度評価】{self.proposal['title']}")
        print(f"{'='*70}\n")

        for sister in ["牡丹", "Kasho", "ユリ"]:
            score = await self.calculate_sister_score(sister)
            if score:
                self.scores[sister] = score
                print(f"\n{sister}の評価:")
                print(f"  重要度: {score.importance}/10")
                print(f"  緊急度: {score.urgency}/10")
                print(f"  得意度: {score.expertise_match}/10")
                print(f"  こだわり: {score.passion}/10")
                print(f"  理由: {score.reason}")
                print(f"  発案希望: {'はい' if score.want_to_propose else 'いいえ'}")

    async def calculate_sister_score(self, sister: str) -> Optional[PriorityScore]:
        """各姉妹のスコア計算"""

        prompt = f"""あなたは{sister}です。

【提案内容】
タイトル: {self.proposal['title']}
説明: {self.proposal.get('description', '')}
提案元: {self.proposal.get('source', '不明')}

{self.get_expertise_profile(sister)}

以下の4つの観点から0-10で評価してください:

1. **重要度**: この提案はどれくらい重要か？
2. **緊急度**: どれくらい急いで討論すべきか？
3. **得意度**: あなたの得意分野にどれくらい関連するか？
4. **こだわり度**: あなたがどれくらい強くこだわるか？

{sister}らしく、あなたの性格と得意分野を反映して評価してください。

JSON形式で回答（他の文章は不要）:
{{
    "importance": 0-10の整数,
    "urgency": 0-10の整数,
    "expertise_match": 0-10の整数,
    "passion": 0-10の整数,
    "reason": "評価理由（{sister}らしく、1-2文で）",
    "want_to_propose": true または false
}}"""

        response = await self.call_ollama(prompt)
        if not response:
            return None

        # Extract JSON from response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start == -1 or end == 0:
                print(f"[ERROR] No JSON in {sister} response")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            return PriorityScore(
                importance=data.get('importance', 5),
                urgency=data.get('urgency', 5),
                expertise_match=data.get('expertise_match', 5),
                passion=data.get('passion', 5),
                reason=data.get('reason', ''),
                want_to_propose=data.get('want_to_propose', False)
            )

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse error for {sister}: {e}")
            return None

    def get_total_score(self) -> float:
        """総合スコア計算"""

        if not all(self.scores.values()):
            return 0.0

        total = 0.0
        count = 0

        for sister, score in self.scores.items():
            if score:
                # 重要度30% + 緊急度30% + 得意度20% + こだわり20%
                sister_score = (
                    score.importance * 0.3 +
                    score.urgency * 0.3 +
                    score.expertise_match * 0.2 +
                    score.passion * 0.2
                )
                total += sister_score
                count += 1

        return total / count if count > 0 else 0.0

    def get_proposer(self) -> str:
        """発案者を決定（最もこだわりが強い姉妹）"""

        max_passion = 0
        proposer = "牡丹"  # Default

        for sister, score in self.scores.items():
            if score and score.passion > max_passion:
                max_passion = score.passion
                proposer = sister

        return proposer


class DiscussionQueue:
    """討論キュー管理システム"""

    def __init__(self):
        self.queue: List[DiscussionQueueItem] = []      # 待機中
        self.archive: List[DiscussionQueueItem] = []    # 無視
        self.history: List[DiscussionQueueItem] = []    # 完了

    async def add_proposal(
        self,
        title: str,
        description: str = "",
        source: str = "unknown"
    ) -> DiscussionQueueItem:
        """提案を追加"""

        proposal = {
            "title": title,
            "description": description,
            "source": source,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        item = DiscussionQueueItem(proposal)

        # 三姉妹が評価
        await item.evaluate_priority()

        # 判定
        decision = self.should_discuss_now(item)

        print(f"\n{'='*70}")
        print(f"【判定結果】")
        print(f"総合スコア: {item.get_total_score():.1f}/10")
        print(f"判定: {decision}")
        print(f"{'='*70}\n")

        if decision == "DISCUSS_NOW":
            print(f"✓ 即座に討論を開始します")
            # TODO: Execute discussion
            self.history.append(item)
            item.status = "completed"
        elif decision == "QUEUE":
            print(f"→ キューに追加します（後で討論）")
            self.queue.append(item)
        else:  # IGNORE
            print(f"✗ 無視します（アーカイブに保存）")
            self.archive.append(item)
            item.status = "ignored"

        return item

    def should_discuss_now(self, item: DiscussionQueueItem) -> str:
        """今討論すべきか判定"""

        total_score = item.get_total_score()

        # スコアリング閾値
        if total_score >= 7.0:
            return "DISCUSS_NOW"  # 即座に討論
        elif total_score >= 4.0:
            return "QUEUE"  # キューに残す（後で）
        else:
            return "IGNORE"  # 無視（アーカイブ）

    def get_queue_summary(self) -> str:
        """キューの状態サマリー"""

        # Sort queue by score
        sorted_queue = sorted(
            self.queue,
            key=lambda x: x.get_total_score(),
            reverse=True
        )

        summary = f"\n{'='*70}\n"
        summary += f"【キュー状態】\n"
        summary += f"{'='*70}\n\n"
        summary += f"待機中: {len(self.queue)}件\n"
        summary += f"アーカイブ: {len(self.archive)}件\n"
        summary += f"完了: {len(self.history)}件\n\n"

        if sorted_queue:
            summary += f"【待機中の議題】（優先度順）\n\n"
            for i, item in enumerate(sorted_queue, 1):
                score = item.get_total_score()
                proposer = item.get_proposer()
                summary += f"{i}. {item.proposal['title']}\n"
                summary += f"   スコア: {score:.1f}/10 | 発案候補: {proposer}\n"
                summary += f"   提案元: {item.proposal['source']}\n\n"

        return summary

    async def process_queue(self):
        """キューを処理（優先度順）"""

        if not self.queue:
            print("キューは空です")
            return

        # Sort by score
        self.queue.sort(
            key=lambda x: x.get_total_score(),
            reverse=True
        )

        print(f"\n{'='*70}")
        print(f"【キュー処理開始】")
        print(f"{'='*70}\n")

        for item in self.queue[:]:  # Copy to avoid modification during iteration
            decision = self.should_discuss_now(item)

            if decision == "DISCUSS_NOW":
                print(f"\n討論開始: {item.proposal['title']}")
                # TODO: Execute discussion
                self.queue.remove(item)
                self.history.append(item)
                item.status = "completed"
            elif decision == "IGNORE":
                print(f"\n無視: {item.proposal['title']}")
                self.queue.remove(item)
                self.archive.append(item)
                item.status = "ignored"


async def test_queue_system():
    """Test the queue system"""

    print("\n" + "="*70)
    print("Phase 1.6+ 優先順位キューシステム - テスト")
    print("="*70 + "\n")

    queue = DiscussionQueue()

    # Test proposals
    test_proposals = [
        {
            "title": "スパチャ読み上げシステムの実装",
            "description": "配信中にスパチャを読み上げる機能がほしい",
            "source": "視聴者 @user123"
        },
        {
            "title": "データベースのバックアップシステム",
            "description": "毎日自動でDBをバックアップする仕組み",
            "source": "開発者"
        },
        {
            "title": "配信で歌ってほしい",
            "description": "カラオケ配信やってほしいです！",
            "source": "視聴者 @user456"
        }
    ]

    for proposal in test_proposals:
        await queue.add_proposal(
            title=proposal['title'],
            description=proposal['description'],
            source=proposal['source']
        )
        print("\n" + "-"*70 + "\n")

    # Summary
    print(queue.get_queue_summary())


if __name__ == "__main__":
    asyncio.run(test_queue_system())
