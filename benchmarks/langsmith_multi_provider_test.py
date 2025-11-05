#!/usr/bin/env python3
"""
LangSmith Multi-Provider Benchmark Test

Tests multiple LLM providers and model sizes with LangSmith tracing:
- Ollama: qwen2.5:3b, 7b, 14b
- OpenAI: gpt-4o-mini
- Gemini: gemini-1.5-flash

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


def run_benchmark():
    """
    Run benchmark across all providers and models
    """
    print("="*60)
    print("  LangSmith Multi-Provider Benchmark")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Test prompt
    test_prompt = "Tell me about AI VTubers in one sentence."

    # Model configurations
    models = [
        {"provider": "ollama", "model": "qwen2.5:3b", "name": "Ollama qwen2.5:3b"},
        {"provider": "ollama", "model": "qwen2.5:7b", "name": "Ollama qwen2.5:7b"},
        {"provider": "ollama", "model": "qwen2.5:14b", "name": "Ollama qwen2.5:14b"},
        {"provider": "openai", "model": "gpt-4o-mini", "name": "OpenAI gpt-4o-mini"},
        {"provider": "gemini", "model": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
    ]

    results = []

    for i, config in enumerate(models, 1):
        print(f"\n[{i}/{len(models)}] Testing: {config['name']}")
        print("-" * 60)

        try:
            # Initialize LLM
            llm = TracedLLM(
                provider=config["provider"],
                model=config["model"],
                project_name="botan-multi-provider-benchmark"
            )

            # Generate
            start_time = time.time()
            result = llm.generate(
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=100,
                metadata={
                    "benchmark": "multi_provider_test",
                    "model_name": config["name"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            elapsed = time.time() - start_time

            # Display result
            print(f"✅ Response: {result['response'][:80]}...")
            print(f"✅ Latency: {result['latency_ms']:.2f}ms (wall time: {elapsed*1000:.2f}ms)")
            print(f"✅ Tokens: {result['tokens']}")

            if 'error' in result:
                print(f"⚠️ Error: {result['error']}")

            results.append({
                "config": config,
                "result": result,
                "success": 'error' not in result
            })

        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            results.append({
                "config": config,
                "result": None,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "="*60)
    print("  Benchmark Summary")
    print("="*60)

    successful = sum(1 for r in results if r['success'])
    print(f"\nTotal tests: {len(models)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(models) - successful}")

    print("\n📊 Latency Comparison:")
    print("-" * 60)
    for r in results:
        if r['success']:
            config = r['config']
            result = r['result']
            latency = result['latency_ms']
            tokens = result['tokens']['total_tokens']
            print(f"{config['name']:25s}: {latency:7.2f}ms ({tokens:3d} tokens)")
        else:
            config = r['config']
            print(f"{config['name']:25s}: FAILED")

    print("\n🔍 Check LangSmith dashboard:")
    print("   https://smith.langchain.com")
    print("   Project: botan-multi-provider-benchmark")
    print("\n✅ All traces have been sent to LangSmith for visualization!")
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
    os.environ["LANGSMITH_PROJECT"] = "botan-multi-provider-benchmark"

    # Run benchmark
    run_benchmark()
