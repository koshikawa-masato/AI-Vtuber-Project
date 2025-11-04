"""Simple WebUI API Test - Single message test"""

import json
import base64
import numpy as np
from scipy.io.wavfile import write
import websocket


def test_simple(message="こんにちは"):
    """Simple test with one message"""

    print("=" * 60)
    print("WebUI API Simple Test")
    print("=" * 60)
    print(f"Message: {message}\n")

    # Storage
    audio_chunks = []
    response_text = ""
    test_done = False

    def on_message(ws, msg):
        nonlocal response_text, test_done

        data = json.loads(msg)

        if data["type"] == "audio_chunk":
            # Decode audio
            audio_bytes = base64.b64decode(data["data"])
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            audio_chunks.append(audio_float32)

            print(f"[AUDIO] Received {len(audio_float32)} samples ({len(audio_float32)/22050:.2f}s)")

        elif data["type"] == "text":
            response_text = data["content"]
            print(f"[TEXT] {response_text}")
            test_done = True
            ws.close()

    def on_error(ws, error):
        print(f"[ERROR] {error}")

    def on_close(ws, code, msg):
        print(f"\n[CLOSED] Connection closed (code: {code})")

    def on_open(ws):
        print("[CONNECTED] Sending message...\n")
        ws.send(json.dumps({
            "type": "message",
            "content": message,
            "voice_enabled": True
        }))

    # Connect (port can be changed via environment variable)
    import os
    port = os.environ.get("WEBUI_PORT", "8888")

    ws = websocket.WebSocketApp(
        f"ws://localhost:{port}/ws",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()

    # Results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Response: {response_text}")
    print(f"Audio chunks: {len(audio_chunks)}")

    if audio_chunks:
        full_audio = np.concatenate(audio_chunks)
        print(f"Total duration: {len(full_audio)/22050:.2f}s")

        output_file = "webui_test_simple.wav"
        write(output_file, 22050, full_audio)
        print(f"✅ Saved: {output_file}")


if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "こんにちは"
    test_simple(msg)
