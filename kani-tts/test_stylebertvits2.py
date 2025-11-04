"""Test Style-Bert-VITS2 Japanese TTS"""

from style_bert_vits2.tts_model import TTSModel

# Load Japanese model
print("Loading Style-Bert-VITS2 model...")
model = TTSModel(
    model_path="litagin/Style-Bert-VITS2-2.0-base-JP-Extra",
    device="cuda"  # or "cpu"
)

# Test Japanese text
test_text = "こんにちは！オジサン！今日も配信がんばってるね〜！"

print(f"Generating audio for: {test_text}")
audio = model.infer(text=test_text)

# Save audio
output_path = "output_style_bert_vits2.wav"
audio.save(output_path)

print(f"Audio saved to: {output_path}")
print("✅ Style-Bert-VITS2 test complete!")
