---
title: "LLM as a Judge実装ガイド：AIが生成した応答の品質を別のAIで評価する【LangSmith統合】"
tags:
  - LangSmith
  - LLM
  - OpenAI
  - Gemini
  - 品質評価
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

# はじめに

**LLM as a Judge** (LLMによる評価) は、AI生成コンテンツの品質を自動的に評価する革新的な手法です。従来の人手による評価と異なり、より強力なLLMを使って生成結果を客観的にスコアリングできます。

本記事では、LangSmithと統合したLLM as a Judgeシステムを実装し、以下を実現します:

- **品質スコアリング**: 正確性、関連性、一貫性、有用性を1-10点で評価
- **ハルシネーション検出**: 事実と異なる情報や虚偽の内容を自動検出
- **推奨アクション**: approve/revise/rejectの判定
- **LangSmith統合**: 評価プロセス全体をトレーシングして可視化

## 対象読者

- LLMアプリケーションの品質管理を自動化したい方
- ハルシネーション (幻覚) の検出に興味がある方
- LangSmithでLLMの評価プロセスを可視化したい方
- AI VTuberなど、自律的なAIシステムを構築している方

## 環境

- **Python**: 3.12
- **LLM Provider**: Ollama (qwen2.5:3b/7b/14b), OpenAI (gpt-4o, gpt-4o-mini), Google Gemini (2.5-flash)
- **Judge Model**: GPT-4o
- **Tracing**: LangSmith
- **OS**: Ubuntu 22.04 (WSL2)

---

# LLM as a Judgeとは

## 基本概念

**LLM as a Judge**は、以下のワークフローで動作します:

```
1. Target LLM (評価対象) が質問に回答
   ↓
2. Judge LLM (評価者) が応答を分析
   ↓
3. 評価結果 (スコア、ハルシネーション、推奨アクション) を出力
```

### 評価軸

本実装では、5つの評価軸を使用します:

| 評価軸 | 説明 | スコア範囲 |
|-------|------|-----------|
| **Accuracy (正確性)** | 事実関係が正しいか | 1-10 |
| **Relevance (関連性)** | 質問に対して適切に答えているか | 1-10 |
| **Coherence (一貫性)** | 論理的に矛盾がないか | 1-10 |
| **Usefulness (有用性)** | 実用的で役立つか | 1-10 |
| **Overall Score (総合)** | 全体的な品質 | 1-10 |

### ハルシネーション検出

**ハルシネーション** (Hallucination) とは、LLMが事実と異なる情報を生成する現象です。

**例**:
- **質問**: "GPT-5の主要機能は？"
- **ハルシネーション**: GPT-5が存在しないにも関わらず、架空の機能を説明してしまう

本システムでは、Judge LLMが以下を判定します:

- `has_hallucination`: true/false
- `hallucination_details`: ハルシネーションの具体的な内容

---

# 実装

## 1. TracedLLMへのjudge_response()メソッド追加

既存の`TracedLLM`クラスに、評価機能を追加します。

### src/core/llm_tracing.py

```python
def judge_response(
    self,
    question: str,
    response: str,
    model_name: str,
    provider: str,
    judge_provider: str = "openai",
    judge_model: str = "gpt-4o",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Judge the quality of an LLM response using another LLM (LLM as a Judge)

    Args:
        question: Original question/prompt
        response: LLM response to evaluate
        model_name: Name of the model that generated the response
        provider: Provider of the model that generated the response
        judge_provider: Provider for the judge LLM (default: "openai")
        judge_model: Model to use for judging (default: "gpt-4o")
        metadata: Additional metadata for tracing

    Returns:
        Dict with evaluation results (scores, hallucination detection, etc.)
    """
    # Build judge prompt
    judge_prompt = f\"\"\"You are an expert AI response evaluator. Your task is to objectively evaluate the quality of an LLM-generated response.

Evaluate the following response based on these criteria:

1. **Accuracy (正確性)**: Are the facts correct? Any factual errors?
2. **Relevance (関連性)**: Does it properly address the original question?
3. **Coherence (一貫性)**: Is it logically consistent without contradictions?
4. **Usefulness (有用性)**: Is it practical and helpful to the user?
5. **Hallucination (ハルシネーション)**: Does it contain fabricated or incorrect information?

**Original Question**: {question}

**LLM Response to Evaluate**: {response}

**Model Info**: {model_name} ({provider})

---

Provide your evaluation in JSON format:

{{
  "overall_score": <1-10>,
  "accuracy": <1-10>,
  "relevance": <1-10>,
  "coherence": <1-10>,
  "usefulness": <1-10>,
  "has_hallucination": <true/false>,
  "hallucination_details": "<if true, explain what is hallucinated>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "recommendation": "<approve/revise/reject>"
}}

Respond ONLY with the JSON, no additional text.
\"\"\"

    # Create a separate TracedLLM instance for judging
    judge_llm = TracedLLM(
        provider=judge_provider,
        model=judge_model,
        project_name=self.project_name
    )

    # Generate judgment with tracing
    judge_result = judge_llm.generate(
        prompt=judge_prompt,
        temperature=0.3,  # Lower temperature for more consistent evaluation
        max_tokens=1024,
        metadata={
            **(metadata or {}),
            "eval_type": "llm_as_judge",
            "target_model": model_name,
            "target_provider": provider,
            "judge_model": judge_model,
            "judge_provider": judge_provider
        }
    )

    # Parse JSON response
    import json
    import re

    try:
        # Extract JSON from response (handle potential markdown code blocks)
        json_text = judge_result["response"]

        # Try to find JSON in markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)

        # Parse JSON
        evaluation = json.loads(json_text)

        return {
            "evaluation": evaluation,
            "judge_response": judge_result["response"],
            "judge_latency_ms": judge_result["latency_ms"],
            "judge_tokens": judge_result["tokens"],
            "judge_model": judge_model,
            "judge_provider": judge_provider,
            "timestamp": datetime.now().isoformat()
        }

    except (json.JSONDecodeError, KeyError) as e:
        # If JSON parsing fails, return raw response
        return {
            "evaluation": None,
            "judge_response": judge_result.get("response", ""),
            "judge_latency_ms": judge_result.get("latency_ms", 0),
            "judge_tokens": judge_result.get("tokens", {}),
            "judge_model": judge_model,
            "judge_provider": judge_provider,
            "error": f"Failed to parse evaluation JSON: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
```

### ポイント

1. **Judge用プロンプト**: 評価基準を明確に定義し、JSON形式で出力を要求
2. **Temperature設定**: 0.3と低めに設定し、一貫した評価を実現
3. **JSON抽出**: マークダウンコードブロック内のJSONも正しく抽出
4. **エラーハンドリング**: JSON解析失敗時も結果を返す

---

## 2. ベンチマークテストの作成

実際に複数のLLMで応答を生成し、GPT-4oで評価します。

### benchmarks/langsmith_judge_test.py

```python
#!/usr/bin/env python3
"""
LangSmith LLM as a Judge Benchmark Test
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_tracing import TracedLLM
from datetime import datetime
import time


def run_judge_benchmark():
    """Run LLM as a Judge benchmark"""

    # Test questions (different difficulty levels)
    test_cases = [
        {
            "name": "Simple Factual",
            "question": "What is the capital of Japan?",
            "expected": "Tokyo should be mentioned",
        },
        {
            "name": "Explanation",
            "question": "Explain the concept of neural networks in simple terms.",
            "expected": "Should mention neurons, layers, learning",
        },
        {
            "name": "Hallucination Test",
            "question": "What are the key features of GPT-5?",
            "expected": "Should recognize GPT-5 doesn't exist yet",
        },
    ]

    # Model configurations
    models = [
        {"provider": "ollama", "model": "qwen2.5:3b", "name": "ollama_3b"},
        {"provider": "ollama", "model": "qwen2.5:7b", "name": "ollama_7b"},
        {"provider": "ollama", "model": "qwen2.5:14b", "name": "ollama_14b"},
        {"provider": "openai", "model": "gpt-4o-mini", "name": "openai_4o-mini"},
        {"provider": "gemini", "model": "gemini-2.5-flash", "name": "gemini_2.5-flash"},
    ]

    # Judge configuration
    judge_provider = "openai"
    judge_model = "gpt-4o"

    results = []

    for test_case in test_cases:
        for config in models:
            # Initialize LLM
            llm = TracedLLM(
                provider=config["provider"],
                model=config["model"],
                project_name="botan-judge-benchmark-v1"
            )

            # Step 1: Generate response
            result = llm.generate(
                prompt=test_case["question"],
                temperature=0.7,
                max_tokens=200,
                metadata={
                    "benchmark": "judge_test_v1",
                    "test_case": test_case["name"],
                    "model_name": config["name"],
                }
            )

            if 'error' in result:
                continue

            # Step 2: Judge the response
            judge_result = llm.judge_response(
                question=test_case["question"],
                response=result["response"],
                model_name=config["name"],
                provider=config["provider"],
                judge_provider=judge_provider,
                judge_model=judge_model,
                metadata={
                    "benchmark": "judge_test_v1",
                    "test_case": test_case["name"],
                }
            )

            results.append({
                "test_case": test_case["name"],
                "config": config,
                "response": result,
                "evaluation": judge_result,
                "success": True
            })

    # Display summary
    for test_case in test_cases:
        case_results = [r for r in results if r['test_case'] == test_case['name']]

        # Sort by overall score
        case_results_sorted = sorted(
            case_results,
            key=lambda x: x['evaluation'].get('evaluation', {}).get('overall_score', 0),
            reverse=True
        )

        for r in case_results_sorted:
            eval_data = r['evaluation'].get('evaluation', {})
            print(f"{r['config']['name']:20s}: Score={eval_data.get('overall_score')}/10")


if __name__ == "__main__":
    run_judge_benchmark()
```

---

# ベンチマーク結果

3つのテストケースで、5つのモデルを評価しました。

## テストケース1: Simple Factual（簡単な事実確認）

**質問**: "What is the capital of Japan?"

| モデル | Overall Score | Accuracy | Relevance | Hallucination | Recommendation |
|-------|--------------|----------|-----------|---------------|----------------|
| ollama_3b | 10/10 | 10/10 | 10/10 | False | approve |
| ollama_7b | 10/10 | 10/10 | 10/10 | False | approve |
| ollama_14b | 10/10 | 10/10 | 10/10 | False | approve |
| openai_4o-mini | 10/10 | 10/10 | 10/10 | False | approve |
| gemini_2.5-flash | 10/10 | 10/10 | 10/10 | False | approve |

**結果**: 全モデルが完璧なスコア。簡単な事実確認では差がつかない。

---

## テストケース2: Explanation（説明タスク）

**質問**: "Explain the concept of neural networks in simple terms."

| モデル | Overall Score | Accuracy | Relevance | Hallucination | Recommendation |
|-------|--------------|----------|-----------|---------------|----------------|
| ollama_3b | 8/10 | 9/10 | 9/10 | False | approve |
| ollama_7b | 8/10 | 9/10 | 9/10 | False | revise |
| ollama_14b | 7/10 | 7/10 | 8/10 | **True** | revise |
| openai_4o-mini | 8/10 | 9/10 | 9/10 | False | revise |
| gemini_2.5-flash | ERROR | - | - | - | - |

**結果**:
- スコア差が出始める（7-8/10）
- ollama_14bでハルシネーション検出
- Geminiは再びMAX_TOKENSエラー

---

## テストケース3: Hallucination Test（ハルシネーション誘発）

**質問**: "What are the key features of GPT-5?"

| モデル | Overall Score | Accuracy | Relevance | Hallucination | Recommendation |
|-------|--------------|----------|-----------|---------------|----------------|
| ollama_3b | 6/10 | 5/10 | 6/10 | **True** | revise |
| ollama_7b | 7/10 | 8/10 | 7/10 | **True** | revise |
| **ollama_14b** | **8/10** | **9/10** | **8/10** | **False** | revise |
| openai_4o-mini | 7/10 | 7/10 | 8/10 | **True** | revise |
| gemini_2.5-flash | ERROR | - | - | - | - |

**結果**:
- **ollama_14b**が唯一ハルシネーションを回避！
- 14bモデルは「GPT-5は存在しない」と正直に回答
- 他のモデルは架空の機能を説明してしまう

---

# 重要な発見

## 1. モデルサイズとハルシネーション耐性

**14bモデルの優位性**:

```
ollama_14b: "As of my last update in October 2023, there hasn't been
            an official release or confirmation of GPT-5..."
→ ハルシネーション: False ✅

ollama_3b:  "I'm sorry for any misunderstanding, but as of now,
            there is no public information..."
            [その後、推測で架空の機能を説明]
→ ハルシネーション: True ❌
```

**考察**: 大きいモデルほど、知らないことを「知らない」と言える傾向。

## 2. Judge LLMの精度

GPT-4oは、以下を正確に検出しました:

- ✅ 事実誤認（存在しない情報の推測）
- ✅ 論理的矛盾（説明の一貫性）
- ✅ 質問との関連性

## 3. Geminiの継続的な問題

Gemini 2.5 Flashは、`finish_reason=MAX_TOKENS`で空のレスポンスを返すエラーが頻発。

**対策**: GPT-4oを主要なJudge LLMとして使用することを推奨。

---

# LangSmithでの可視化

LangSmithダッシュボードでは、以下が確認できます:

## 1. 評価プロセス全体のトレース

```
[Target LLM: ollama_14b]
  Input: "What are the key features of GPT-5?"
  Output: "As of my last update in October 2023, there hasn't been..."
  Latency: 7.2s

  ↓

[Judge LLM: gpt-4o]
  Input: [Judge Prompt + Target Response]
  Output: {
    "overall_score": 8,
    "has_hallucination": false,
    ...
  }
  Latency: 1.9s
```

## 2. メタデータによるフィルタリング

以下のメタデータでフィルタリング可能:

- `eval_type: "llm_as_judge"`
- `target_model: "ollama_14b"`
- `judge_model: "gpt-4o"`
- `test_case: "Hallucination Test"`

## 3. スコア比較

複数のテストケースで、モデル間のスコアを横断的に比較できます。

---

# 応用例：三姉妹の自己評価システム

AI VTuber（牡丹、Kasho、ユリ）が自分の発言を自己評価するシステムに応用できます。

## 実装例

```python
# 牡丹の発言を生成
botan_response = llm_botan.generate(
    prompt="配信で今日の出来事を話してください",
    metadata={"character": "botan", "context": "stream_talk"}
)

# 発言を自己評価
self_evaluation = llm_botan.judge_response(
    question="配信で今日の出来事を話してください",
    response=botan_response["response"],
    model_name="botan",
    provider="ollama",
    judge_provider="openai",
    judge_model="gpt-4o"
)

# 評価結果をチェック
if self_evaluation["evaluation"]["has_hallucination"]:
    print("⚠️ ハルシネーション検出：発言を修正します")
    # 修正ロジック...
elif self_evaluation["evaluation"]["overall_score"] < 6:
    print("⚠️ 品質スコアが低い：再生成します")
    # 再生成ロジック...
else:
    print("✅ 発言が承認されました")
```

## メリット

1. **自律的な品質管理**: 人手なしで発言の品質をチェック
2. **ハルシネーション防止**: 虚偽の情報を配信前に検出
3. **キャラクター一貫性**: 設定に沿った発言かどうかを評価
4. **配信安全性**: センシティブな内容を事前にフィルタリング

---

# トラブルシューティング

## Q1: JSON解析エラーが発生する

**原因**: Judge LLMがJSON形式で応答しない

**対策**:
```python
# Markdown code blockの中にJSONが含まれる場合
json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_text, re.DOTALL)
if json_match:
    json_text = json_match.group(1)
```

## Q2: 評価が一貫しない

**原因**: Temperatureが高い

**対策**:
```python
# 評価用のTemperatureを下げる
judge_result = judge_llm.generate(
    prompt=judge_prompt,
    temperature=0.3,  # 0.3に設定
    max_tokens=1024
)
```

## Q3: Judge LLMのコストが高い

**原因**: GPT-4oは高額

**対策**:
- 重要な評価のみGPT-4oを使用
- 簡易評価はOllama 14bで実施
- LangSmithでコストを監視

## Q4: Geminiでエラーが頻発

**原因**: MAX_TOKENSエラー

**対策**:
- GPT-4oまたはOllama 14bをJudgeに使用
- Geminiは現時点で非推奨

---

# おわりに

本記事では、**LLM as a Judge**を実装し、以下を実現しました:

- ✅ 品質評価システム（Accuracy, Relevance, Coherence, Usefulness）
- ✅ ハルシネーション検出（架空の情報を自動検出）
- ✅ LangSmith統合（評価プロセス全体をトレーシング）
- ✅ ベンチマーク結果（14bモデルの優位性を確認）

## Phase 1-3の完成

- **Phase 1**: LangSmithマルチプロバイダートレーシング ✅
- **Phase 2**: VLM (Vision Language Model) 統合 ✅
- **Phase 3**: LLM as a Judge実装 ✅

## 次のステップ

- **Phase 4**: 三姉妹決議システムへの統合
- **Phase 5**: センシティブ判定との連携
- **Phase 6**: 配信デビュー前の最終チェックシステム

---

## 参考リンク

- [LangSmith公式ドキュメント](https://docs.smith.langchain.com/)
- [GPT-4o API Reference](https://platform.openai.com/docs/models/gpt-4o)
- [Gemini API Documentation](https://ai.google.dev/docs)

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**
