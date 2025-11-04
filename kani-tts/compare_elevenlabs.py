"""Compare KaniTTS vs ElevenLabs - Botan Voice Quality Test"""

import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

# Load environment variables
env_path = Path("/home/koshikawa/botan-ai-chatbot/.env")
load_dotenv(env_path)


class ElevenLabsComparison:
    def __init__(self):
        """Initialize ElevenLabs client"""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in .env file")

        self.client = ElevenLabs(api_key=self.api_key)

        # Voice settings from .env
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "B8gJV1IhpuegLxdpXFOE")
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_v3")

        self.voice_settings = VoiceSettings(
            stability=float(os.getenv("ELEVENLABS_STABILITY", "0.5")),
            similarity_boost=float(os.getenv("ELEVENLABS_SIMILARITY", "0.75")),
            style=float(os.getenv("ELEVENLABS_STYLE", "0.75")),
            use_speaker_boost=True
        )

        print(f"[INFO] ElevenLabs initialized")
        print(f"[INFO] Voice ID: {self.voice_id}")
        print(f"[INFO] Model: {self.model}")

    def generate_speech(self, text: str, output_path: str):
        """Generate speech using ElevenLabs API"""
        try:
            start_time = time.time()

            # Remove "botan:" prefix for ElevenLabs
            clean_text = text.replace("botan:", "").strip()

            # Generate speech
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                output_format="mp3_44100_128",
                text=clean_text,
                model_id=self.model,
                voice_settings=self.voice_settings
            )

            # Save to file
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            total_time = time.time() - start_time

            # Get file size
            file_size = os.path.getsize(output_path) / 1024  # KB

            return {
                'success': True,
                'total_time': total_time,
                'file_size': file_size,
                'output_path': output_path
            }

        except Exception as e:
            print(f"[ERROR] ElevenLabs generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    print("="*80)
    print("ElevenLabs vs KaniTTS Comparison - Botan Voice Test")
    print("="*80)

    # Test prompts (same as KaniTTS test)
    test_prompts = [
        ("A-1", "botan: あ、おはよー！"),
        ("A-2", "botan: マジで？"),
        ("B-1", "botan: やったー！最高じゃん！"),
        ("B-2", "botan: え、マジ！？うそでしょ！？"),
        ("C-1", "botan: えっとね、これはね、すごく大事なやつなんだよね。いつも使ってるやつ。"),
    ]

    # Initialize ElevenLabs
    try:
        eleven_client = ElevenLabsComparison()
    except Exception as e:
        print(f"[ERROR] Failed to initialize ElevenLabs: {e}")
        print("\nPlease check:")
        print("1. .env file exists at /home/koshikawa/botan-ai-chatbot/.env")
        print("2. ELEVENLABS_API_KEY is set and valid")
        print("3. Internet connection is available")
        sys.exit(1)

    results = []

    print("\n" + "="*80)
    print("Generating ElevenLabs Audio...")
    print("="*80)

    for i, (category, prompt) in enumerate(test_prompts, 1):
        print(f"\n[Test {i}/{len(test_prompts)}] [{category}]: {prompt}")
        print("-" * 80)

        output_file = f'output_elevenlabs_{i}_{category}.mp3'

        result = eleven_client.generate_speech(prompt, output_file)

        if result['success']:
            print(f"✅ Success!")
            print(f"   Time: {result['total_time']:.2f}s")
            print(f"   Size: {result['file_size']:.1f} KB")
            print(f"   File: {result['output_path']}")
            results.append(result)
        else:
            print(f"❌ Failed: {result['error']}")

    # Summary
    print("\n" + "="*80)
    print("ELEVENLABS GENERATION SUMMARY")
    print("="*80)

    if results:
        avg_time = sum(r['total_time'] for r in results) / len(results)
        avg_size = sum(r['file_size'] for r in results) / len(results)

        print(f"\nTotal tests: {len(results)}/{len(test_prompts)}")
        print(f"Average generation time: {avg_time:.2f}s")
        print(f"Average file size: {avg_size:.1f} KB")

        print("\n" + "="*80)
        print("COMPARISON NOTES")
        print("="*80)
        print("\n⚠️  Direct latency comparison is difficult:")
        print("   - ElevenLabs: API call time (network + generation)")
        print("   - KaniTTS: Local generation only (no network)")
        print("\n📊 Audio Quality Comparison:")
        print("   - Listen to both sets of audio files")
        print("   - Compare naturalness, clarity, emotion")
        print("\n📁 Generated files:")
        print("   - ElevenLabs: output_elevenlabs_*.mp3")
        print("   - KaniTTS: output_450m_*.wav")

    else:
        print("\n❌ No audio files were generated successfully")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
