"""WebUI WebSocket API Test - Test without browser"""

import json
import base64
import time
import numpy as np
from scipy.io.wavfile import write
import websocket
from pathlib import Path


def decode_audio_chunk(base64_data):
    """Decode base64 audio chunk to numpy array"""
    # Decode base64 to bytes
    audio_bytes = base64.b64decode(base64_data)

    # Convert bytes to int16 array
    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

    # Convert int16 to float32 (-1.0 to 1.0)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    return audio_float32


def test_webui_api(message, voice_enabled=True, save_audio=True):
    """Test WebUI WebSocket API"""

    print("=" * 80)
    print("WebUI WebSocket API Test")
    print("=" * 80)
    print(f"\nTest message: {message}")
    print(f"Voice enabled: {voice_enabled}")
    print(f"Save audio: {save_audio}")
    print()

    # WebSocket URL (port can be changed via environment variable)
    import os
    port = os.environ.get("WEBUI_PORT", "8888")
    ws_url = f"ws://localhost:{port}/ws"

    # Storage for audio chunks
    audio_chunks = []
    response_text = ""

    # WebSocket event handlers
    def on_message(ws, message):
        nonlocal response_text

        data = json.loads(message)

        if data["type"] == "audio_chunk":
            print(f"[RECEIVED] Audio chunk (base64 length: {len(data['data'])})")

            # Decode audio chunk
            audio_chunk = decode_audio_chunk(data["data"])
            audio_chunks.append(audio_chunk)

            duration = len(audio_chunk) / data["sample_rate"]
            print(f"           Duration: {duration:.2f}s, Sample rate: {data['sample_rate']} Hz")

        elif data["type"] == "text":
            response_text = data["content"]
            print(f"\n[RECEIVED] Text response: {response_text}")

        elif data["type"] == "error":
            print(f"\n[ERROR] {data['message']}")

    def on_error(ws, error):
        print(f"[ERROR] WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"\n[CLOSED] WebSocket connection closed")
        print(f"          Status code: {close_status_code}")
        if close_msg:
            print(f"          Message: {close_msg}")

    def on_open(ws):
        print(f"[CONNECTED] WebSocket connection established")
        print(f"            URL: {ws_url}")

        # Send message
        request = {
            "type": "message",
            "content": message,
            "voice_enabled": voice_enabled
        }

        print(f"\n[SENDING] Message: {json.dumps(request, ensure_ascii=False)}")
        ws.send(json.dumps(request))

    # Create WebSocket connection
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Run WebSocket client
    print(f"\n[CONNECTING] Attempting to connect to {ws_url}...")
    ws.run_forever()

    # Process results
    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)

    print(f"\nResponse text: {response_text}")
    print(f"Audio chunks received: {len(audio_chunks)}")

    if audio_chunks and save_audio:
        # Concatenate all audio chunks
        full_audio = np.concatenate(audio_chunks)
        total_duration = len(full_audio) / 22050

        print(f"Total audio duration: {total_duration:.2f}s")
        print(f"Total samples: {len(full_audio)}")

        # Save to WAV file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"webui_test_{timestamp}.wav"
        write(output_file, 22050, full_audio)

        print(f"\n✅ Audio saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Test completed")
    print("=" * 80)


def run_multiple_tests():
    """Run multiple test cases"""

    test_cases = [
        ("こんにちは", True),
        ("牡丹プロジェクトって何？", True),
        ("短いテスト", False),  # Voice OFF
    ]

    for i, (message, voice_enabled) in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# Test Case {i}/{len(test_cases)}")
        print(f"{'#' * 80}\n")

        test_webui_api(message, voice_enabled=voice_enabled)

        # Wait between tests
        if i < len(test_cases):
            print("\nWaiting 3 seconds before next test...")
            time.sleep(3)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Single test with custom message
        message = " ".join(sys.argv[1:])
        test_webui_api(message, voice_enabled=True)
    else:
        # Run all test cases
        print("Running multiple test cases...")
        print("(Use: python test_webui_api.py 'your message' for single test)\n")
        run_multiple_tests()
