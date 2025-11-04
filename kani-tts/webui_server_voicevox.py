"""WebUI Chat Server with VOICEVOX Japanese TTS"""

import asyncio
import base64
import json
import requests
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import numpy as np

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "elyza:botan_custom"

# VOICEVOX configuration
VOICEVOX_URL = "http://localhost:50021"
VOICEVOX_SPEAKER = 72  # 満別花丸 - ぶりっ子（ギャルっぽい）
VOICEVOX_SPEED = 1.0  # 通常速度


def generate_botan_response(user_message: str, chat_history: list = None) -> str:
    """Generate Botan's response using Ollama LLM"""
    if chat_history is None:
        chat_history = []

    chat_history.append({
        "role": "user",
        "content": user_message
    })

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": chat_history,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            botan_reply = result.get("message", {}).get("content", "")

            chat_history.append({
                "role": "assistant",
                "content": botan_reply
            })

            return botan_reply.strip()
        else:
            print(f"[LLM ERROR] Ollama returned status {response.status_code}")
            return "あれ〜？ちょっと調子悪いかも...ごめんね！"

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "え〜、なんか固まっちゃった...ごめん！"


def generate_voicevox_audio(text: str, speaker_id: int = VOICEVOX_SPEAKER) -> bytes:
    """Generate audio using VOICEVOX"""
    try:
        # Step 1: Create audio query
        query_response = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=5
        )

        if query_response.status_code != 200:
            print(f"[VOICEVOX ERROR] Query failed: {query_response.status_code}")
            return b""

        audio_query = query_response.json()

        # Adjust speed
        audio_query["speedScale"] = VOICEVOX_SPEED

        # Step 2: Synthesize speech
        synthesis_response = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": speaker_id},
            json=audio_query,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if synthesis_response.status_code != 200:
            print(f"[VOICEVOX ERROR] Synthesis failed: {synthesis_response.status_code}")
            return b""

        return synthesis_response.content

    except Exception as e:
        print(f"[VOICEVOX ERROR] {e}")
        return b""


app = FastAPI(title="Botan WebUI Chat with VOICEVOX")

# Chat history storage
chat_sessions = {}


@app.get("/")
async def get():
    """Serve HTML interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>牡丹チャット - VOICEVOX</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .chat-container {
                width: 90%;
                max-width: 800px;
                height: 90vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
            }
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 20px 20px 0 0;
                font-size: 24px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .voice-toggle {
                padding: 10px 20px;
                border: 2px solid white;
                border-radius: 25px;
                background: transparent;
                color: white;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .voice-toggle.on {
                background: white;
                color: #667eea;
            }
            .voice-toggle:hover {
                transform: scale(1.05);
            }
            .messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .message {
                margin-bottom: 15px;
                display: flex;
                animation: fadeIn 0.3s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .message.user {
                justify-content: flex-end;
            }
            .message-content {
                max-width: 70%;
                padding: 12px 18px;
                border-radius: 18px;
                word-wrap: break-word;
            }
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .message.assistant .message-content {
                background: white;
                color: #333;
                border: 2px solid #e0e0e0;
            }
            .input-area {
                display: flex;
                padding: 20px;
                background: white;
                border-radius: 0 0 20px 20px;
                border-top: 2px solid #e0e0e0;
            }
            #user-input {
                flex: 1;
                padding: 12px 18px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s;
            }
            #user-input:focus {
                border-color: #667eea;
            }
            #send-btn {
                margin-left: 10px;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            #send-btn:hover {
                transform: scale(1.05);
            }
            #send-btn:active {
                transform: scale(0.95);
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                🌸 牡丹チャット (満別花丸 - ぶりっ子)
                <button class="voice-toggle on" id="voice-toggle">Voice ON</button>
            </div>
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <input type="text" id="user-input" placeholder="メッセージを入力..." autofocus>
                <button id="send-btn">送信</button>
            </div>
        </div>

        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const messagesDiv = document.getElementById('messages');
            const userInput = document.getElementById('user-input');
            const sendBtn = document.getElementById('send-btn');
            const voiceToggle = document.getElementById('voice-toggle');

            let voiceEnabled = true;
            let audioContext = null;

            // Initialize Web Audio API
            function initAudio() {
                if (!audioContext) {
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
            }

            // Voice toggle
            voiceToggle.addEventListener('click', () => {
                voiceEnabled = !voiceEnabled;
                voiceToggle.textContent = voiceEnabled ? 'Voice ON' : 'Voice OFF';
                voiceToggle.className = voiceEnabled ? 'voice-toggle on' : 'voice-toggle';

                if (voiceEnabled) {
                    initAudio();
                }
            });

            // Play WAV audio
            async function playAudio(base64Data) {
                if (!voiceEnabled || !audioContext) return;

                try {
                    // Decode base64 to ArrayBuffer
                    const binaryString = atob(base64Data);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }

                    // Decode audio data
                    const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);

                    // Play audio
                    const source = audioContext.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(audioContext.destination);
                    source.start();
                } catch (error) {
                    console.error('Audio playback error:', error);
                }
            }

            // WebSocket handlers
            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'text') {
                    addMessage(data.content, 'assistant');
                } else if (data.type === 'audio') {
                    await playAudio(data.data);
                } else if (data.type === 'error') {
                    console.error('Error:', data.message);
                }
            };

            // Send message
            function sendMessage() {
                const message = userInput.value.trim();
                if (!message) return;

                addMessage(message, 'user');
                ws.send(JSON.stringify({
                    type: 'message',
                    content: message,
                    voice_enabled: voiceEnabled
                }));

                userInput.value = '';
            }

            function addMessage(content, role) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = content;

                messageDiv.appendChild(contentDiv);
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            sendBtn.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });

            ws.onopen = () => {
                console.log('Connected to server');
                initAudio();
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('Disconnected from server');
            };
        </script>
    </body>
    </html>
    """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEBSOCKET] Client connected")

    # Initialize chat history
    session_id = id(websocket)
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                user_message = data["content"]
                voice_enabled = data.get("voice_enabled", True)

                print(f"[WEBSOCKET] User: {user_message}, Voice: {voice_enabled}")

                # Generate Botan's response using LLM
                loop = asyncio.get_event_loop()
                botan_response = await loop.run_in_executor(
                    None,
                    generate_botan_response,
                    user_message,
                    chat_sessions[session_id]
                )

                print(f"[LLM] Botan: {botan_response}")

                # Send text response first
                await websocket.send_json({
                    "type": "text",
                    "content": botan_response
                })

                # Generate and send audio if voice is enabled
                if voice_enabled:
                    audio_data = await loop.run_in_executor(
                        None,
                        generate_voicevox_audio,
                        botan_response
                    )

                    if audio_data:
                        # Send audio as base64
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio",
                            "data": audio_base64
                        })
                        print(f"[VOICEVOX] Audio sent ({len(audio_data)} bytes)")
                    else:
                        print("[VOICEVOX] Audio generation failed")

    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected")
        if session_id in chat_sessions:
            del chat_sessions[session_id]
    except Exception as e:
        print(f"[WEBSOCKET] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888

    print(f"\n{'='*60}")
    print("Starting Botan WebUI Server with VOICEVOX")
    print(f"Access at: http://localhost:{port}")
    print("="*60)

    uvicorn.run(app, host="0.0.0.0", port=port)
