"""Test Streaming Playback - Real-time audio generation and playback"""

import time
from audio import LLMAudioPlayer, StreamingAudioPlayerWriter
from generation import TTSGenerator
from config import CHUNK_SIZE, LOOKBACK_FRAMES

from nemo.utils.nemo_logging import Logger

nemo_logger = Logger()
nemo_logger.remove_stream_handlers()


def main():
    print("="*80)
    print("KaniTTS Streaming Playback Test - Real-time Generation & Playback")
    print("="*80)

    # Initialize generator
    print("\nInitializing generator...")
    generator = TTSGenerator()
    player = LLMAudioPlayer(generator.tokenizer)

    # Test prompts
    test_prompts = [
        ("Short", "botan: マジで？"),
        ("Medium", "botan: やったー！最高じゃん！めっちゃ嬉しい！"),
        ("Long", "botan: えっとね、これはね、すごく大事なやつなんだよね。いつも使ってるやつ。"),
    ]

    for i, (label, prompt) in enumerate(test_prompts, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_prompts)} [{label}]")
        print(f"Prompt: {prompt}")
        print('='*80)
        print("\n🔊 Audio will play in real-time as it's being generated...")
        print("   (You should hear the voice immediately, not after completion)")

        output_file = f'output_streaming_{i}_{label.lower()}.wav'

        # Create streaming audio player+writer with real-time playback
        audio_writer = StreamingAudioPlayerWriter(
            player,
            output_file,
            chunk_size=CHUNK_SIZE,
            lookback_frames=LOOKBACK_FRAMES,
            enable_playback=True  # Enable real-time playback
        )
        audio_writer.start()

        # Generate speech
        start_time = time.time()
        result = generator.generate(prompt, audio_writer)

        # Finalize (this will wait for playback to finish)
        audio = audio_writer.finalize()

        total_time = time.time() - start_time

        if audio is not None:
            audio_duration = len(audio) / 22050
            print(f"\n✅ Complete!")
            print(f"   Audio duration: {audio_duration:.2f}s")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Saved to: {output_file}")
        else:
            print(f"\n❌ Failed to generate audio")

        # Short pause between tests
        if i < len(test_prompts):
            print("\nWaiting 2 seconds before next test...")
            time.sleep(2)

    print("\n" + "="*80)
    print("All streaming playback tests completed!")
    print("="*80)

    print("\n📝 Notes:")
    print("   - Audio should have played in real-time during generation")
    print("   - First chunk may have slight delay (initial processing)")
    print("   - Subsequent chunks should play immediately")
    print("   - All audio files were saved simultaneously")


if __name__ == "__main__":
    main()
