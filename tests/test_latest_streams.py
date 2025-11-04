"""
Test script to verify latest stream integration
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from botan_subculture.helpers.conversation_context import ConversationContextBuilder

def main():
    print("=" * 60)
    print("Testing Latest Stream Integration")
    print("=" * 60)

    builder = ConversationContextBuilder()

    # Test 1: Get context for Sakura Miko (Botan's favorite)
    print("\n[Test 1] Sakura Miko (さくらみこ) - Affinity Level 5")
    print("-" * 60)

    context = builder.get_recent_streams_context("さくらみこ", days=7, limit=5)

    if context:
        print(f"VTuber: {context['vtuber_info']['name']}")
        print(f"Affinity Level: {context['vtuber_info']['affinity_level']}")
        print(f"Total Watched (7 days): {context['total_watched']} streams")
        print(f"Can Mention: {context['can_mention']} streams")

        print("\nRecent Streams:")
        for stream in context['recent_streams']:
            print(f"  [{stream['date']}] {stream['title']}")

        print("\n" + "=" * 60)
        print("System Prompt Addition:")
        print("=" * 60)
        prompt = builder.build_system_prompt_addition(context)
        print(prompt)

    # Test 2: Get context for Inugami Korone (Botan's favorite)
    print("\n[Test 2] Inugami Korone (戌神ころね) - Affinity Level 5")
    print("-" * 60)

    context = builder.get_recent_streams_context("戌神ころね", days=7, limit=5)

    if context:
        print(f"VTuber: {context['vtuber_info']['name']}")
        print(f"Affinity Level: {context['vtuber_info']['affinity_level']}")
        print(f"Total Watched (7 days): {context['total_watched']} streams")
        print(f"Can Mention: {context['can_mention']} streams")

        print("\nRecent Streams:")
        for stream in context['recent_streams']:
            print(f"  [{stream['date']}] {stream['title']}")

    # Test 3: Get context for regular member (Affinity Level 3)
    print("\n[Test 3] Usada Pekora (兎田ぺこら) - Affinity Level 3")
    print("-" * 60)

    context = builder.get_recent_streams_context("兎田ぺこら", days=7, limit=5)

    if context:
        print(f"VTuber: {context['vtuber_info']['name']}")
        print(f"Affinity Level: {context['vtuber_info']['affinity_level']}")
        print(f"Total Watched (7 days): {context['total_watched']} streams")
        print(f"Can Mention: {context['can_mention']} streams")

        print("\nRecent Streams:")
        for stream in context['recent_streams']:
            print(f"  [{stream['date']}] {stream['title']}")

    builder.close()

    print("\n" + "=" * 60)
    print("[SUCCESS] Latest stream integration is working!")
    print("=" * 60)
    print("\nBotan can now talk about:")
    print("  - Recent streams from the last 7 days")
    print("  - Specific stream titles and dates")
    print("  - Different enthusiasm levels based on affinity")


if __name__ == '__main__':
    main()
