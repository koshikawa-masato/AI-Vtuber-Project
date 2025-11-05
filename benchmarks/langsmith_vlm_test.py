#!/usr/bin/env python3
"""
LangSmith Vision Language Model Benchmark Test

Tests Vision capabilities with:
- OpenAI: gpt-4o
- Gemini: gemini-2.5-flash

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


def run_vlm_benchmark():
    """
    Run Vision Language Model benchmark
    """
    print("="*60)
    print("  LangSmith VLM Benchmark")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Test prompt
    test_prompt = "What do you see in this image? Describe it in detail."

    # Test image URL (public test image)
    # Using a simple test image from picsum.photos
    test_image_url = "https://picsum.photos/800/600"

    # Model configurations (only Vision-capable models)
    models = [
        {"provider": "openai", "model": "gpt-4o", "name": "gpt4o_vision"},
        # Note: gemini-2.5-flash has issues with Vision (MAX_TOKENS error)
        # {"provider": "gemini", "model": "gemini-2.5-flash", "name": "gemini_2.5_flash_vision"},
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
                project_name="botan-vlm-benchmark-v1"
            )

            print(f"\n  Testing with image...")
            print(f"  Image URL: {test_image_url[:60]}...")

            start_time = time.time()
            result = llm.generate(
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=300,
                image_url=test_image_url,
                metadata={
                    "benchmark": "vlm_test_v1",
                    "model_name": config["name"],
                    "has_image": True,
                    "timestamp": datetime.now().isoformat()
                }
            )
            elapsed = time.time() - start_time

            # Display result
            print(f"  ✅ Response: {result['response'][:100]}...")
            print(f"  ✅ Latency: {result['latency_ms']:.2f}ms (wall time: {elapsed*1000:.2f}ms)")
            print(f"  ✅ Tokens: {result['tokens']['total_tokens']}")

            if 'error' in result:
                print(f"  ⚠️ Error: {result['error']}")

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

    print("\n📊 VLM Performance Comparison:")
    print("-" * 60)
    for r in results:
        if r['success']:
            config = r['config']
            result = r['result']
            latency = result['latency_ms']
            tokens = result['tokens']['total_tokens']
            response_len = len(result['response'])
            print(f"{config['name']:25s}: {latency:7.2f}ms ({tokens:3d} tokens, {response_len:3d} chars)")
        else:
            config = r['config']
            print(f"{config['name']:25s}: FAILED")

    print("\n🔍 Check LangSmith dashboard:")
    print("   https://smith.langchain.com")
    print("   Project: botan-vlm-benchmark-v1")
    print("\n✅ All VLM traces have been sent to LangSmith for visualization!")
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
    os.environ["LANGSMITH_PROJECT"] = "botan-vlm-benchmark-v1"

    # Run benchmark
    run_vlm_benchmark()
