"""KaniTTS Performance Benchmark"""

import time
import torch
import psutil
import os
from audio import LLMAudioPlayer, StreamingAudioWriter
from generation import TTSGenerator
from config import CHUNK_SIZE, LOOKBACK_FRAMES

from nemo.utils.nemo_logging import Logger

nemo_logger = Logger()
nemo_logger.remove_stream_handlers()


def get_gpu_memory():
    """Get GPU memory usage in MB"""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024 / 1024
    return 0


def get_process_memory():
    """Get process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def benchmark_prompt(generator, player, prompt, output_file):
    """Benchmark a single prompt"""
    # Memory before
    gpu_mem_before = get_gpu_memory()
    proc_mem_before = get_process_memory()

    # Create audio writer
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

    # Finalize
    audio = audio_writer.finalize()
    end_time = time.time()

    # Memory after
    gpu_mem_after = get_gpu_memory()
    proc_mem_after = get_process_memory()

    # Calculate metrics
    total_time = end_time - start_time
    model_time = result['point_2'] - result['point_1']
    codec_time = end_time - result['point_2']

    # Get audio file size
    file_size = os.path.getsize(output_file) / 1024  # KB

    # Get audio duration from file name or estimate
    audio_duration = len(audio) / 22050  # samples / sample_rate

    return {
        'prompt': prompt,
        'audio_duration': audio_duration,
        'total_time': total_time,
        'model_time': model_time,
        'codec_time': codec_time,
        'file_size': file_size,
        'gpu_mem_used': gpu_mem_after - gpu_mem_before,
        'proc_mem_used': proc_mem_after - proc_mem_before,
        'latency_ratio': total_time / audio_duration if audio_duration > 0 else 0,
        'tokens_generated': result.get('total_tokens', 0)
    }


def main():
    print("="*80)
    print("KaniTTS Performance Benchmark - RTX 4060 Ti 16GB")
    print("="*80)

    # System info
    print(f"\nSystem Information:")
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  CUDA: {torch.version.cuda}")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CPU Cores: {psutil.cpu_count()}")
    print(f"  Total RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")

    # Initialize
    print("\nInitializing generator...")
    init_start = time.time()
    generator = TTSGenerator()
    player = LLMAudioPlayer(generator.tokenizer)
    init_time = time.time() - init_start
    print(f"  Initialization time: {init_time:.2f}s")
    print(f"  GPU memory after init: {get_gpu_memory():.1f} MB")

    # Test prompts (various lengths)
    test_cases = [
        ("Short", "botan: うん、わかった。"),
        ("Medium", "botan: あ、オジサン、おはよー！今日も開発するの？"),
        ("Long", "botan: ねえねえ、オジサン、これ見て見て！すごくない？マジでヤバいんだけど！"),
        ("Very Long", "botan: うーん、難しいなぁ。でも面白そう！これってつまり、AIが自分で学習して、どんどん賢くなっていくってこと？すごい時代だよね。"),
    ]

    results = []

    print("\n" + "="*80)
    print("Running Benchmarks...")
    print("="*80)

    for i, (label, prompt) in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}] {label}")
        print(f"Prompt: {prompt}")
        print("-" * 80)

        output_file = f'benchmark_{i}_{label.lower().replace(" ", "_")}.wav'
        result = benchmark_prompt(generator, player, prompt, output_file)
        results.append((label, result))

        # Print immediate results
        print(f"  Audio duration: {result['audio_duration']:.2f}s")
        print(f"  Total time: {result['total_time']:.2f}s")
        print(f"  Model time: {result['model_time']:.2f}s")
        print(f"  Codec time: {result['codec_time']:.2f}s")
        print(f"  Latency ratio: {result['latency_ratio']:.2f}x")
        print(f"  File size: {result['file_size']:.1f} KB")
        print(f"  Tokens: {result['tokens_generated']}")
        print(f"  GPU memory: {result['gpu_mem_used']:.1f} MB")

    # Summary
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)

    print(f"\n{'Test':<15} {'Audio(s)':<10} {'Total(s)':<10} {'Ratio':<10} {'Tokens':<10} {'GPU(MB)':<10}")
    print("-" * 80)

    for label, result in results:
        print(f"{label:<15} {result['audio_duration']:<10.2f} {result['total_time']:<10.2f} "
              f"{result['latency_ratio']:<10.2f} {result['tokens_generated']:<10} "
              f"{result['gpu_mem_used']:<10.1f}")

    # Calculate averages
    avg_latency = sum(r['latency_ratio'] for _, r in results) / len(results)
    avg_model_time = sum(r['model_time'] for _, r in results) / len(results)
    avg_codec_time = sum(r['codec_time'] for _, r in results) / len(results)
    max_gpu_mem = max(r['gpu_mem_used'] for _, r in results)

    print("\n" + "="*80)
    print("KEY METRICS")
    print("="*80)
    print(f"  Average latency ratio: {avg_latency:.2f}x")
    print(f"  Average model time: {avg_model_time:.2f}s")
    print(f"  Average codec time: {avg_codec_time:.2f}s")
    print(f"  Max GPU memory used: {max_gpu_mem:.1f} MB")
    print(f"  Total GPU memory: {get_gpu_memory():.1f} MB")

    # Comparison with ElevenLabs (estimated)
    print("\n" + "="*80)
    print("COMPARISON WITH ELEVENLABS (ESTIMATED)")
    print("="*80)
    print("  ElevenLabs API latency: ~1.5-3.0s (network + generation)")
    print(f"  KaniTTS local latency: {avg_latency:.2f}x realtime")
    print("  KaniTTS advantage: No network latency, no API costs")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    if avg_latency < 1.0:
        print("  ✅ EXCELLENT: Faster than realtime generation")
        print("  → Ready for production use")
    elif avg_latency < 1.5:
        print("  ✅ GOOD: Near-realtime generation")
        print("  → Suitable for most use cases")
    else:
        print("  ⚠️  MODERATE: Slower than realtime")
        print("  → Consider optimization or pre-generation")

    if max_gpu_mem < 4000:
        print(f"  ✅ Low GPU memory usage ({max_gpu_mem:.1f} MB)")
        print("  → Can run alongside other GPU tasks")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
