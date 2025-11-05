#!/usr/bin/env python3
"""
Three Sisters Discussion System Benchmark

Tests the three sisters discussing various topics:
- Technical decisions (LLM selection, architecture)
- Content creation (stream ideas, video topics)
- Policy decisions (community rules, moderation)

All traces sent to LangSmith dashboard.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_tracing import ThreeSistersTracedCouncil
from datetime import datetime


def run_discussion_benchmark():
    """
    Run three sisters discussion benchmark
    """
    print("="*60)
    print("  Three Sisters Discussion System Benchmark")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Initialize council
    council = ThreeSistersTracedCouncil(
        model="qwen2.5:14b",
        project_name="botan-three-sisters-discussion-v1"
    )

    # Test topics
    test_topics = [
        {
            "name": "Technical Decision",
            "topic": "Should we use GPT-4o or Gemini for our stream chat responses?",
            "rounds": 2
        },
        {
            "name": "Content Creation",
            "topic": "What should be the theme of our first collaborative stream?",
            "rounds": 2
        },
        {
            "name": "Community Policy",
            "topic": "How should we handle negative comments in our chat?",
            "rounds": 2
        },
    ]

    results = []

    for idx, test_case in enumerate(test_topics, 1):
        print(f"\n{'#'*60}")
        print(f"Test Case {idx}/{len(test_topics)}: {test_case['name']}")
        print(f"Topic: {test_case['topic']}")
        print(f"{'#'*60}")

        try:
            # Run discussion
            result = council.discuss(
                topic=test_case['topic'],
                rounds=test_case['rounds']
            )

            results.append({
                "test_case": test_case["name"],
                "topic": test_case["topic"],
                "result": result,
                "success": True
            })

            print(f"\n✅ Discussion completed: {result['total_exchanges']} exchanges")

        except Exception as e:
            print(f"\n❌ Discussion failed: {str(e)}")
            results.append({
                "test_case": test_case["name"],
                "topic": test_case["topic"],
                "result": None,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "="*60)
    print("  Benchmark Summary")
    print("="*60)

    successful = sum(1 for r in results if r['success'])
    print(f"\nTotal discussions: {len(test_topics)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(test_topics) - successful}")

    print("\n📊 Discussion Statistics:")
    print("-" * 60)
    for r in results:
        if r['success']:
            result_data = r['result']
            print(f"\n{r['test_case']:30s}")
            print(f"  Topic: {r['topic']}")
            print(f"  Total exchanges: {result_data['total_exchanges']}")
            print(f"  Participants: {', '.join(result_data['participants'])}")
            print(f"  Consensus preview: {result_data['consensus'][:100]}...")
        else:
            print(f"\n{r['test_case']:30s}: FAILED")

    print("\n🔍 Check LangSmith dashboard:")
    print("   https://smith.langchain.com")
    print("   Project: botan-three-sisters-discussion-v1")
    print("\n✅ All discussion traces have been sent to LangSmith!")
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
    os.environ["LANGSMITH_PROJECT"] = "botan-three-sisters-discussion-v1"

    # Run benchmark
    run_discussion_benchmark()
