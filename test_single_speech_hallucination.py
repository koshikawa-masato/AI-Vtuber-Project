#!/usr/bin/env python3
"""
Test Single Speech for Hallucination Detection
牡丹のRound 1発言をテスト

Author: Claude Code
Date: 2025-10-24
"""

from hallucination_personalizer import HallucinationPersonalizer

COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"

# 牡丹のRound 1発言（明らかにInspiration型のはず）
BOTAN_ROUND1 = """この議題について、私は賛成だと思う。なぜなら、次に何をやってみたいかを考えるだけでもワクワクするよね！ねぇねぇ、もし私たち三姉妹で新しい料理教室を開くとしたら、どんなメニューを教えていこうかな？ Kasho姉はきっと美味しいレシピを持っていて、ユリも一緒に参加してくれるはずだよね！これを実現できたら、みんなが喜んでくれると思うから、とっても嬉しい気持ちになるだろうな。"""

def test_single_speech():
    """単一発言をテスト"""

    print("=" * 80)
    print("Single Speech Hallucination Test")
    print("=" * 80)
    print()

    print("Testing speech:")
    print("-" * 80)
    print(BOTAN_ROUND1)
    print("-" * 80)
    print()

    # Initialize personalizer
    print("[1] Initializing HallucinationPersonalizer...")
    personalizer = HallucinationPersonalizer(
        memory_db_path=COPY_ROBOT_DB,
        enable_logging=True
    )
    print("   ✅ Initialized")
    print()

    # Process the speech
    print("[2] Processing speech...")
    result = personalizer.process_response(
        character='botan',
        llm_response=BOTAN_ROUND1,
        context={'phase': '起', 'round': 1, 'test': True}
    )

    print()
    print("=" * 80)
    print("Result")
    print("=" * 80)
    print()
    print(f"Is Hallucination: {result['is_hallucination']}")
    print(f"Hallucination Type: {result.get('hallucination_type', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
    print()

    if result['is_hallucination']:
        print("✅ Hallucination detected!")
        print()
        print(f"Type: {result['hallucination_type']}")
        print()

        if result['hallucination_type'] == 'inspiration':
            print("🌟 This is an Inspiration!")
            print(f"   Aspirational Value: {result.get('aspirational_value', 'N/A')}")
            print()
    else:
        print("❌ No hallucination detected")
        print()
        print("Possible reasons:")
        print("  - Statement is factually consistent with memory")
        print("  - HallucinationDetector didn't trigger")
        print("  - Detection threshold too high")
        print()

    print("=" * 80)


if __name__ == '__main__':
    test_single_speech()
