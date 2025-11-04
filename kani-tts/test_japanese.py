"""KaniTTS Japanese Test - Botan Voice Test"""

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
    report = f"SPEECH TOKENS: {model_request:.2f}\nCODEC: {player_time:.2f}\nTOTAL: {total_time:.2f}"
    return report


def main():
    # Initialize generator and audio player
    generator = TTSGenerator()
    player = LLMAudioPlayer(generator.tokenizer)

    # Japanese test prompts (Botan-style)
    test_prompts = [
        "botan: あ、オジサン、おはよー！",
        "botan: うん、わかった。マジで？",
        "botan: そうなんだ。えー、ヤバくない？",
        "botan: ねえねえ、オジサン、これ見て見て！",
        "botan: うーん、難しいなぁ。でも面白そう！"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_prompts)}: {prompt}")
        print('='*60)

        # Create streaming audio writer with sliding window decoder
        output_file = f'output_japanese_{i}.wav'
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
        print(f"Output: {output_file}")
        print(f"Total time: {point_3 - start_time:.2f}s")


if __name__ == "__main__":
    main()
