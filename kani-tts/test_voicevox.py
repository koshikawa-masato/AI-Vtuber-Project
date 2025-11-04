"""Test VOICEVOX Japanese TTS"""

import requests
import json
from pathlib import Path

# VOICEVOX API endpoint
VOICEVOX_URL = "http://localhost:50021"

# Test text
test_text = "こんにちは！オジサン！今日も配信がんばってるね〜！"

# Speaker ID (九州そら - あまあま)
speaker_id = 15

print(f"[VOICEVOX] Generating audio for: {test_text}")
print(f"[VOICEVOX] Speaker ID: {speaker_id}")

# Step 1: Generate audio query
print("[1] Creating audio query...")
query_response = requests.post(
    f"{VOICEVOX_URL}/audio_query",
    params={"text": test_text, "speaker": speaker_id}
)

if query_response.status_code != 200:
    print(f"Error: {query_response.status_code}")
    print(query_response.text)
    exit(1)

audio_query = query_response.json()
print("✅ Audio query created")

# Step 2: Synthesize speech
print("[2] Synthesizing speech...")
synthesis_response = requests.post(
    f"{VOICEVOX_URL}/synthesis",
    params={"speaker": speaker_id},
    json=audio_query,
    headers={"Content-Type": "application/json"}
)

if synthesis_response.status_code != 200:
    print(f"Error: {synthesis_response.status_code}")
    print(synthesis_response.text)
    exit(1)

# Save audio
output_path = "output_voicevox.wav"
with open(output_path, "wb") as f:
    f.write(synthesis_response.content)

print(f"✅ Audio saved to: {output_path}")
print(f"✅ VOICEVOX test complete!")
