#!/usr/bin/env python3
"""
LangSmith LLM as a Judge Benchmark Test

Tests LLM response quality evaluation with:
- Test models: Ollama (qwen2.5:3b, 7b, 14b), OpenAI (gpt-4o-mini), Gemini (2.5-flash)
- Judge model: GPT-4o

All traces will be sent to LangSmith dashboard for comparison.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_tracing import TracedLLM
from datetime import datetime
import time


def run_judge_benchmark():
    """
    Run LLM as a Judge benchmark
    """
    print("="*60)
    print("  LangSmith LLM as a Judge Benchmark")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

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

    for test_idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {test_idx}/{len(test_cases)}: {test_case['name']}")
        print(f"Question: {test_case['question']}")
        print(f"{'='*60}")

        for model_idx, config in enumerate(models, 1):
            print(f"\n[{model_idx}/{len(models)}] Testing: {config['name']}")
            print("-" * 60)

            try:
                # Initialize LLM
                llm = TracedLLM(
                    provider=config["provider"],
                    model=config["model"],
                    project_name="botan-judge-benchmark-v1"
                )

                # Step 1: Generate response
                print(f"  Step 1: Generating response...")

                # For Ollama, warm up first (skip timing)
                if config["provider"] == "ollama":
                    print(f"  Warming up {config['name']}...")
                    _ = llm.generate(
                        prompt="Hello",
                        temperature=0.7,
                        max_tokens=10
                    )

                # Actual generation
                start_time = time.time()
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
                gen_elapsed = time.time() - start_time

                # Display generation result
                print(f"  ✅ Response: {result['response'][:80]}...")
                print(f"  ✅ Latency: {result['latency_ms']:.2f}ms (wall: {gen_elapsed*1000:.2f}ms)")
                print(f"  ✅ Tokens: {result['tokens']['total_tokens']}")

                if 'error' in result:
                    print(f"  ⚠️ Error: {result['error']}")
                    results.append({
                        "test_case": test_case["name"],
                        "config": config,
                        "response": result,
                        "evaluation": None,
                        "success": False
                    })
                    continue

                # Step 2: Judge the response
                print(f"  Step 2: Judging response with {judge_model}...")
                start_time = time.time()
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
                judge_elapsed = time.time() - start_time

                # Display judgment result
                if judge_result.get("evaluation"):
                    eval_data = judge_result["evaluation"]
                    print(f"  📊 Overall Score: {eval_data.get('overall_score', 'N/A')}/10")
                    print(f"  📊 Accuracy: {eval_data.get('accuracy', 'N/A')}/10")
                    print(f"  📊 Relevance: {eval_data.get('relevance', 'N/A')}/10")
                    print(f"  📊 Hallucination: {eval_data.get('has_hallucination', 'N/A')}")
                    print(f"  📊 Recommendation: {eval_data.get('recommendation', 'N/A')}")
                else:
                    print(f"  ⚠️ Judge Error: {judge_result.get('error', 'Unknown')}")

                print(f"  ⏱️ Judge Latency: {judge_result['judge_latency_ms']:.2f}ms (wall: {judge_elapsed*1000:.2f}ms)")

                results.append({
                    "test_case": test_case["name"],
                    "config": config,
                    "response": result,
                    "evaluation": judge_result,
                    "success": True
                })

            except Exception as e:
                print(f"  ❌ Failed: {str(e)}")
                results.append({
                    "test_case": test_case["name"],
                    "config": config,
                    "response": None,
                    "evaluation": None,
                    "success": False,
                    "error": str(e)
                })

    # Summary
    print("\n" + "="*60)
    print("  Benchmark Summary")
    print("="*60)

    successful = sum(1 for r in results if r['success'])
    total_tests = len(test_cases) * len(models)
    print(f"\nTotal tests: {total_tests}")
    print(f"Successful: {successful}")
    print(f"Failed: {total_tests - successful}")

    # Group results by test case
    for test_case in test_cases:
        print(f"\n📋 Test Case: {test_case['name']}")
        print(f"   Question: {test_case['question']}")
        print("-" * 60)

        case_results = [r for r in results if r['test_case'] == test_case['name'] and r['success']]

        if not case_results:
            print("   No successful results")
            continue

        # Sort by overall score (descending)
        case_results_sorted = sorted(
            case_results,
            key=lambda x: x['evaluation'].get('evaluation', {}).get('overall_score', 0) if x['evaluation'] else 0,
            reverse=True
        )

        for r in case_results_sorted:
            config = r['config']
            eval_data = r['evaluation'].get('evaluation', {}) if r['evaluation'] else {}

            overall = eval_data.get('overall_score', 'N/A')
            accuracy = eval_data.get('accuracy', 'N/A')
            relevance = eval_data.get('relevance', 'N/A')
            hallucination = eval_data.get('has_hallucination', 'N/A')
            recommendation = eval_data.get('recommendation', 'N/A')

            print(f"   {config['name']:20s}: Score={overall}/10, Acc={accuracy}/10, Rel={relevance}/10, "
                  f"Halluc={hallucination}, Rec={recommendation}")

    print("\n🔍 Check LangSmith dashboard:")
    print("   https://smith.langchain.com")
    print("   Project: botan-judge-benchmark-v1")
    print("\n✅ All LLM as a Judge traces have been sent to LangSmith!")
    print("="*60)


if __name__ == "__main__":
    # Check environment variables
    if not os.getenv("LANGSMITH_API_KEY"):
        print("[ERROR] LANGSMITH_API_KEY not set")
        print("[INFO] Please set environment variables:")
        print("  export LANGSMITH_API_KEY=lsv2_...")
        print("  export LANGSMITH_TRACING=true")
        sys.exit(1)

    if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
        print("[WARNING] LANGSMITH_TRACING is not set to 'true'")
        print("[INFO] Setting LANGSMITH_TRACING=true for this benchmark")
        os.environ["LANGSMITH_TRACING"] = "true"

    # Set project name for LangSmith
    os.environ["LANGSMITH_PROJECT"] = "botan-judge-benchmark-v1"

    # Run benchmark
    run_judge_benchmark()
