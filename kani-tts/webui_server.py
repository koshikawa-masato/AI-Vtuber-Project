"""WebUI Chat Server with Streaming Voice Playback"""

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub.utils")
warnings.filterwarnings("ignore", message=".*torch_dtype.*deprecated.*")
warnings.filterwarnings("ignore", message=".*Couldn't find ffmpeg.*")

import asyncio
import base64
import json
import requests
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from pathlib import Path

from audio import LLMAudioPlayer
from generation import TTSGenerator
from config import CHUNK_SIZE, LOOKBACK_FRAMES, SAMPLE_RATE

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "elyza:botan_custom"

from nemo.utils.nemo_logging import Logger
nemo_logger = Logger()
nemo_logger.remove_stream_handlers()


def generate_botan_response(user_message: str, chat_history: list = None) -> str:
    """Generate Botan's response using Ollama LLM"""
    if chat_history is None:
        chat_history = []

    # Add user message to chat history
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

            # Add assistant response to chat history
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


app = FastAPI(title="KaniTTS WebUI Chat")

# Initialize TTS components
generator = TTSGenerator()
player = LLMAudioPlayer(generator.tokenizer)

# Chat history storage (in-memory for now)
chat_sessions = {}


class WebSocketAudioStreamer:
    """Streams audio chunks to WebSocket client in real-time"""

    def __init__(self, websocket: WebSocket, loop, enable_voice: bool = True):
        self.websocket = websocket
        self.loop = loop  # Event loop for asyncio operations
        self.enable_voice = enable_voice
        self.audio_chunks = []
        self.inside_speech = False
        self.audio_token_buffer = []
        self.all_tokens = []
        self.frames_decoded = 0
        self.ws_queue = asyncio.Queue()  # Queue for WebSocket messages

    def add_token(self, token_id):
        """Add a token and decode/stream audio chunks (synchronous)"""
        # Check for start/end of speech markers
        if token_id == player.start_of_speech:
            print(f"[STREAMING] START_OF_SPEECH detected")
            self.inside_speech = True
            self.audio_token_buffer = []
            return

        if token_id == player.end_of_speech:
            print(f"[STREAMING] END_OF_SPEECH detected")

            # Decode any remaining frames
            total_frames = len(self.all_tokens) // 4
            remaining_frames = total_frames - self.frames_decoded

            if remaining_frames >= 1:
                start_frame = max(0, self.frames_decoded - LOOKBACK_FRAMES)
                start_token = start_frame * 4

                tokens_to_decode = self.all_tokens[start_token:]
                num_frames = len(tokens_to_decode) // 4

                if num_frames > 0:
                    codes = np.array(tokens_to_decode[:num_frames * 4]).reshape(-1, 4)
                    audio_chunk = player.decode_audio_chunk(codes)

                    if audio_chunk is not None:
                        samples_per_frame = len(audio_chunk) // num_frames
                        lookback_skip = min(self.frames_decoded, LOOKBACK_FRAMES)
                        skip_samples = lookback_skip * samples_per_frame
                        new_audio = audio_chunk[skip_samples:]

                        self.audio_chunks.append(new_audio)

                        # Queue final chunk for WebSocket
                        if self.enable_voice:
                            self._queue_audio_chunk(new_audio)

                        print(f"[STREAMING] Final chunk: {remaining_frames} frames")

            self.inside_speech = False
            self.audio_token_buffer = []
            return

        # Accumulate audio tokens
        if self.inside_speech:
            self.audio_token_buffer.append(token_id)
            self.all_tokens.append(token_id)

            # Decode when we have enough NEW frames to process
            total_frames = len(self.all_tokens) // 4
            new_frames = total_frames - self.frames_decoded

            if new_frames >= CHUNK_SIZE:
                start_frame = max(0, self.frames_decoded - LOOKBACK_FRAMES)
                start_token = start_frame * 4

                tokens_to_decode = self.all_tokens[start_token:]
                num_frames = len(tokens_to_decode) // 4

                codes = np.array(tokens_to_decode[:num_frames * 4]).reshape(-1, 4)
                audio_chunk = player.decode_audio_chunk(codes)

                if audio_chunk is not None:
                    samples_per_frame = len(audio_chunk) // num_frames
                    lookback_skip = min(self.frames_decoded, LOOKBACK_FRAMES)
                    skip_samples = lookback_skip * samples_per_frame
                    new_samples = CHUNK_SIZE * samples_per_frame
                    new_audio = audio_chunk[skip_samples:skip_samples + new_samples]

                    self.audio_chunks.append(new_audio)
                    self.frames_decoded += CHUNK_SIZE

                    # Queue chunk for WebSocket
                    if self.enable_voice:
                        self._queue_audio_chunk(new_audio)
                        print(f"[STREAMING] Queued {CHUNK_SIZE} frames ({CHUNK_SIZE/12.5:.2f}s audio)")

                self.audio_token_buffer = []

    def _queue_audio_chunk(self, audio_chunk: np.ndarray):
        """Queue audio chunk for WebSocket transmission (thread-safe)"""
        # Convert float32 to int16 PCM
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Put in queue (will be sent by async task)
        asyncio.run_coroutine_threadsafe(
            self.ws_queue.put({
                "type": "audio_chunk",
                "data": audio_b64,
                "sample_rate": SAMPLE_RATE
            }),
            self.loop
        )

    async def send_queued_chunks(self):
        """Send all queued audio chunks to WebSocket"""
        while True:
            try:
                message = await asyncio.wait_for(self.ws_queue.get(), timeout=0.1)
                await self.websocket.send_json(message)
            except asyncio.TimeoutError:
                break

    def get_full_audio(self) -> Optional[np.ndarray]:
        """Get concatenated full audio"""
        if self.audio_chunks:
            return np.concatenate(self.audio_chunks)
        return None


@app.get("/", response_class=HTMLResponse)
async def get_chat_ui():
    """Serve the chat UI"""
    html_path = Path(__file__).parent / "webui_chat.html"
    if html_path.exists():
        return html_path.read_text()

    # Fallback: return embedded HTML
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KaniTTS Chat</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            #chat-container { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 20px; }
            .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
            .user { background: #e3f2fd; text-align: right; }
            .assistant { background: #f5f5f5; }
            #input-container { display: flex; gap: 10px; margin-bottom: 10px; }
            #user-input { flex: 1; padding: 10px; font-size: 16px; }
            #send-btn { padding: 10px 20px; font-size: 16px; background: #2196F3; color: white; border: none; cursor: pointer; }
            #voice-toggle { padding: 10px 20px; font-size: 16px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            #voice-toggle.off { background: #9E9E9E; }
        </style>
    </head>
    <body>
        <h1>KaniTTS Chat</h1>
        <div id="chat-container"></div>
        <div id="input-container">
            <input type="text" id="user-input" placeholder="Type your message..." />
            <button id="send-btn">Send</button>
            <button id="voice-toggle" class="on">Voice ON</button>
        </div>
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const chatContainer = document.getElementById('chat-container');
            const userInput = document.getElementById('user-input');
            const sendBtn = document.getElementById('send-btn');
            const voiceToggle = document.getElementById('voice-toggle');

            let voiceEnabled = true;
            let audioContext = null;
            let audioQueue = [];
            let isPlaying = false;

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
                voiceToggle.className = voiceEnabled ? 'on' : 'off';

                if (voiceEnabled) {
                    initAudio();
                }
            });

            // Play audio chunk
            async function playAudioChunk(base64Data, sampleRate) {
                if (!voiceEnabled || !audioContext) return;

                // Decode base64 to ArrayBuffer
                const binaryString = atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                // Convert Int16 PCM to Float32
                const int16Array = new Int16Array(bytes.buffer);
                const float32Array = new Float32Array(int16Array.length);
                for (let i = 0; i < int16Array.length; i++) {
                    float32Array[i] = int16Array[i] / 32768.0;
                }

                // Create AudioBuffer
                const audioBuffer = audioContext.createBuffer(1, float32Array.length, sampleRate);
                audioBuffer.getChannelData(0).set(float32Array);

                // Schedule playback
                audioQueue.push(audioBuffer);
                if (!isPlaying) {
                    playNextChunk();
                }
            }

            function playNextChunk() {
                if (audioQueue.length === 0) {
                    isPlaying = false;
                    return;
                }

                isPlaying = true;
                const buffer = audioQueue.shift();
                const source = audioContext.createBufferSource();
                source.buffer = buffer;
                source.connect(audioContext.destination);
                source.onended = () => playNextChunk();
                source.start();
            }

            // WebSocket handlers
            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'text') {
                    addMessage(data.content, 'assistant');
                } else if (data.type === 'audio_chunk') {
                    await playAudioChunk(data.data, data.sample_rate);
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
                const div = document.createElement('div');
                div.className = `message ${role}`;
                div.textContent = content;
                chatContainer.appendChild(div);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            sendBtn.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });

            // Initialize audio on first user interaction
            document.addEventListener('click', initAudio, { once: true });
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEBSOCKET] Client connected")

    # Initialize chat history for this session
    session_id = id(websocket)
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    try:
        while True:
            # Receive message from client
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

                # Prepare prompt for TTS
                prompt = f"botan: {botan_response}"

                # Continue with TTS generation
                # Run generation in thread pool executor

                # Create audio streamer with event loop
                audio_streamer = WebSocketAudioStreamer(websocket, loop, enable_voice=voice_enabled)

                # Start background task to send audio chunks
                generation_done = asyncio.Event()

                async def send_audio_task():
                    while not generation_done.is_set():
                        try:
                            message = await asyncio.wait_for(audio_streamer.ws_queue.get(), timeout=0.1)
                            await websocket.send_json(message)
                        except asyncio.TimeoutError:
                            continue

                    # Send remaining chunks after generation is done
                    while not audio_streamer.ws_queue.empty():
                        message = await audio_streamer.ws_queue.get()
                        await websocket.send_json(message)

                audio_task = asyncio.create_task(send_audio_task())

                # Generate speech (runs in thread pool)
                result = await loop.run_in_executor(
                    None,
                    generator.generate,
                    prompt,
                    audio_streamer
                )

                # Signal that generation is done
                generation_done.set()

                # Wait for all audio chunks to be sent
                await audio_task

                # Send text response (use LLM-generated response)
                await websocket.send_json({
                    "type": "text",
                    "content": botan_response
                })

                print(f"[WEBSOCKET] Assistant: {botan_response}")

    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    import sys

    # Port can be specified via command line: python webui_server.py 8888
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888

    print(f"\n{'='*60}")
    print(f"Starting KaniTTS WebUI Server")
    print(f"Access at: http://localhost:{port}")
    print(f"{'='*60}\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
