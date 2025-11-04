"""KaniTTS 450M-0.2-FT Model Test - Botan Voice"""

import time
from audio import LLMAudioPlayer, StreamingAudioWriter
from generation import TTSGenerator
from config import CHUNK_SIZE, LOOKBACK_FRAMES

from nemo.utils.nemo_logging import Logger

nemo_logger = Logger()
nemo_logger.remove_stream_handlers()


def time_report(point_1, point_2, point_3):
    model_request = point_2 - point_1
    player_time = point_3 - point_2
    total_time = point_3 - point_1
    report = f"SPEECH TOKENS: {model_request:.2f}s\nCODEC: {player_time:.2f}s\nTOTAL: {total_time:.2f}s"
    return report


def main():
    print("="*80)
    print("KaniTTS 450M-0.2-FT Model Test - Botan Voice")
    print("="*80)

    # Initialize generator with 450M-0.2-FT model
    print("\nInitializing generator with kani-tts-450m-0.2-ft model...")
    init_start = time.time()

    # Override model name
    import config
    original_model = config.MODEL_NAME
    config.MODEL_NAME = "nineninesix/kani-tts-450m-0.2-ft"

    generator = TTSGenerator()
    player = LLMAudioPlayer(generator.tokenizer)

    init_time = time.time() - init_start
    print(f"Initialization time: {init_time:.2f}s")
    print(f"Model: {config.MODEL_NAME}")

    # Test prompts from Botan script (Category A & B)
    test_prompts = [
        # Category A: Basic Tone
        ("A-1", "botan: あ、おはよー！"),
        ("A-2", "botan: マジで？"),
        ("A-3", "botan: これって何？"),

        # Category B: Emotions
        ("B-1", "botan: やったー！最高じゃん！"),
        ("B-2", "botan: え、マジ！？うそでしょ！？"),
        ("B-3", "botan: え、ちょっと待って...よくわかんないんだけど..."),
        ("B-4", "botan: もう！何言ってんの〜？"),
        ("B-5", "botan: あ、ヤバ...マジでヤバいんだけど！"),

        # Category C: Long sentences
        ("C-1", "botan: えっとね、これはね、すごく大事なやつなんだよね。いつも使ってるやつ。"),
        ("C-2", "botan: え、何それ！めっちゃ面白そうじゃん！私もやってみたい！教えて教えて！"),
    ]

    results = []

    for i, (category, prompt) in enumerate(test_prompts, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_prompts)} [{category}]: {prompt}")
        print('='*80)

        # Create streaming audio writer
        output_file = f'output_450m_{i}_{category}.wav'
        audio_writer = StreamingAudioWriter(
            player,
            output_file,
            chunk_size=CHUNK_SIZE,
            lookback_frames=LOOKBACK_FRAMES
        )
        audio_writer.start()

        # Generate speech
        start_time = time.time()
        result = generator.generate(prompt, audio_writer)

        # Finalize and write audio file
        audio = audio_writer.finalize()

        point_3 = time.time()

        # Print results
        print(time_report(result['point_1'], result['point_2'], point_3))

        audio_duration = len(audio) / 22050
        latency_ratio = (point_3 - start_time) / audio_duration if audio_duration > 0 else 0

        print(f"Output: {output_file}")
        print(f"Audio duration: {audio_duration:.2f}s")
        print(f"Latency ratio: {latency_ratio:.2f}x")

        results.append({
            'category': category,
            'audio_duration': audio_duration,
            'total_time': point_3 - start_time,
            'latency_ratio': latency_ratio
        })

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY - kani-tts-450m-0.2-ft")
    print("="*80)

    print(f"\n{'Category':<10} {'Audio(s)':<12} {'Total(s)':<12} {'Latency':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['category']:<10} {r['audio_duration']:<12.2f} {r['total_time']:<12.2f} {r['latency_ratio']:<10.2f}")

    avg_latency = sum(r['latency_ratio'] for r in results) / len(results)
    print(f"\nAverage latency ratio: {avg_latency:.2f}x")

    if avg_latency < 1.0:
        print("✅ EXCELLENT: Faster than realtime")
    elif avg_latency < 1.5:
        print("✅ GOOD: Near-realtime")
    else:
        print("⚠️  MODERATE: Slower than realtime")

    # Restore original model name
    config.MODEL_NAME = original_model

    print("\n" + "="*80)
    print("All audio files generated successfully!")
    print("Files: output_450m_1_A-1.wav to output_450m_10_C-2.wav")
    print("="*80)


if __name__ == "__main__":
    main()
