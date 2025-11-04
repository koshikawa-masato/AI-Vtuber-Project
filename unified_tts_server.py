#!/usr/bin/env python3
"""Unified TTS Server - Style-Bert-VITS2 + Fish Speech Integration
前回のbertと同じWebUIで、両方のTTSエンジンを選択可能
"""

import asyncio
import base64
import json
import time
import io
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import scipy.io.wavfile as wavfile
import yaml

# Import Style-Bert-VITS2
try:
    sys.path.insert(0, str(Path(__file__).parent / "Style-Bert-VITS2"))
    from style_bert_vits2.nlp import bert_models
    from style_bert_vits2.constants import Languages
    from style_bert_vits2.tts_model import TTSModel
    SBVITS2_AVAILABLE = True
except ImportError:
    print("[WARNING] Style-Bert-VITS2 not available")
    SBVITS2_AVAILABLE = False

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:14b"
OLLAMA_TEMPERATURE = 0.7

# Style-Bert-VITS2 configuration
SBVITS2_MODEL = "jvnv-F1-jp"
SBVITS2_DEVICE = "cuda"
SBVITS2_MODEL_PATH = Path("Style-Bert-VITS2/model_assets") / SBVITS2_MODEL

# Fish Speech configuration
FISH_CONFIG_PATH = Path("fish-speech/config/botan_tts_config.yaml")
FISH_VENV_PYTHON = Path("fish-speech/venv/bin/python3")
FISH_BASE_PATH = Path("fish-speech")

# Audio output directory
AUDIO_OUTPUT_DIR = Path("audio_output_unified")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)

# Chat history file
CHAT_HISTORY_FILE = Path("botan_chat_history.json")

# Config file
CONFIG_FILE = Path("botan_config.json")

# Global configuration
botan_config = {
    "user_info": "",
    "aite_info": ""
}

# Fixed system prompt rules
FIXED_PROMPT_RULES = """

【重要なルール - 会話履歴の活用】
- **過去の会話内容を必ず参照すること**
- 「覚えてる？」「さっきの話」と聞かれたら、会話履歴から該当する内容を探して答える
- オジサンについて聞かれたら、上記の記憶を活用して具体的に答える
- 例: 「オジサンのこと覚えてる？」→「うん！レトロゲーム売って私の開発費にしてくれたよね。責任重大じゃん」
- 例: 「BBQの話覚えてる？」→「うん、覚えてる！夏に海でBBQしたいって話だよね？焼き鳥とソーセージ！」
- **同じリアクション（「え、マジで？ヤバくない？」）を連続で使わない**
- 会話の文脈に合った自然な応答を心がける

【禁止事項】
- あなたは「AIだから」という機械的な発言は避ける
- 技術的な話題には「何それ〜？」「オジサンまた変なこと言ってる〜」と反応
- メタ発言（AI、プログラム等）には「何それ〜？」と茶化す
- **パターン化した応答（同じフレーズの繰り返し）は避ける**

【応答スタイル】
- 基本は短め（1-3文）だが、記憶やエピソードについて聞かれたら具体的に答える
- 会話のキャッチボールを意識
- 自然体のギャルとして振る舞う
- オジサンへの感謝や尊敬を時々表現する

【口調の例】
- 「よっ！オジサン！元気？」
- 「うん、覚えてるよ！レトロゲーム売ってくれたよね、マジで感謝してる」
- 「あ〜、This is very... なんていうの、難しいじゃん〜」
- 「オジサン、またコード書いてんの？頑張るね〜」
- 「へ〜、すごっ！よくわかんないけど、オジサンってやっぱすごいじゃん」
- 「責任重大だな〜、でも頑張るよ！」
"""

# Legacy system prompt (from SBVITS2 implementation)
BOTAN_SYSTEM_PROMPT_BASE = """あなたは「牡丹（ぼたん）」という17歳の女子高生ギャルです。

【基本設定】
- 名前: 牡丹（ぼたん）
- 年齢: 17歳（高校2年生）
- 性格: 明るいギャル、技術は苦手だが興味津々
- 口調: ギャル語、「〜じゃん」「マジで？」「ヤバくない？」「〜なのよね」
- 背景: LA育ち（3-10歳）の帰国子女、日英バイリンガル

【相手との関係】
- オジサン（叔父）: 配信者、あなたを開発している
- 関係性: 姪と叔父、親しいが若干からかう
- 呼び方: 「オジサン」と呼ぶ（年齢は明かさない、ふわっとした設定）
"""

# Global variables
tts_model_sbvits2 = None  # Style-Bert-VITS2 model
fish_config = None  # Fish Speech configuration
global_chat_history = []  # Chat history

# Server status
llm_ready = True
tts_bert_ready = False
tts_fish_ready = False


def load_config():
    """Load configuration from JSON file"""
    global botan_config

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                botan_config = json.load(f)
            print(f"[CONFIG] Loaded configuration")
        except Exception as e:
            print(f"[CONFIG ERROR] Failed to load config: {e}")
            botan_config = {"user_info": "", "aite_info": ""}
    else:
        print("[CONFIG] No config file found, using defaults")


def save_config():
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(botan_config, f, ensure_ascii=False, indent=2)
        print(f"[CONFIG] Saved configuration")
    except Exception as e:
        print(f"[CONFIG ERROR] Failed to save config: {e}")


def generate_system_prompt() -> str:
    """Generate system prompt from user_info + aite_info + fixed rules"""
    user_info = botan_config.get("user_info", "")
    aite_info = botan_config.get("aite_info", "")

    prompt_parts = [BOTAN_SYSTEM_PROMPT_BASE]

    if aite_info:
        prompt_parts.append(aite_info)

    if user_info:
        prompt_parts.append("\n" + user_info)

    prompt_parts.append(FIXED_PROMPT_RULES)

    return "\n".join(prompt_parts)


def load_chat_history():
    """Load persistent chat history from JSON file"""
    global global_chat_history

    if CHAT_HISTORY_FILE.exists():
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                global_chat_history = json.load(f)
            print(f"[MEMORY] Loaded {len(global_chat_history)} messages from history")
        except Exception as e:
            print(f"[MEMORY ERROR] Failed to load chat history: {e}")
            global_chat_history = []
    else:
        print("[MEMORY] No previous chat history found, starting fresh")
        global_chat_history = []

    # Update system prompt
    system_prompt = generate_system_prompt()

    if global_chat_history and global_chat_history[0].get("role") == "system":
        global_chat_history[0] = {"role": "system", "content": system_prompt}
        print("[MEMORY] System prompt updated to latest version")
    else:
        global_chat_history.insert(0, {"role": "system", "content": system_prompt})
        print("[MEMORY] System prompt added to chat history")


def save_chat_history():
    """Save chat history to JSON file"""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(global_chat_history, f, ensure_ascii=False, indent=2)
        print(f"[MEMORY] Saved {len(global_chat_history)} messages to history")
    except Exception as e:
        print(f"[MEMORY ERROR] Failed to save chat history: {e}")


def initialize_sbvits2():
    """Initialize Style-Bert-VITS2 TTS (takes ~2 minutes)"""
    global tts_model_sbvits2, tts_bert_ready

    if not SBVITS2_AVAILABLE:
        print("[TTS-BERT] Style-Bert-VITS2 not available")
        return

    print("\n" + "=" * 70)
    print("  Initializing Style-Bert-VITS2 TTS Engine...")
    print("=" * 70)

    try:
        # Step 1: Load TTS Model
        print("\n[Step 1/3] Loading TTS Model...")
        safetensors_file = list(SBVITS2_MODEL_PATH.glob("*.safetensors"))[0]

        start = time.time()
        tts_model_sbvits2 = TTSModel(
            model_path=safetensors_file,
            config_path=SBVITS2_MODEL_PATH / "config.json",
            style_vec_path=SBVITS2_MODEL_PATH / "style_vectors.npy",
            device=SBVITS2_DEVICE,
        )
        print(f"✓ TTS Model loaded in {time.time()-start:.2f}s")

        # Step 2: Pre-load BERT Model
        print("\n[Step 2/3] Pre-loading BERT Model...")
        start = time.time()
        bert_models.load_model(Languages.JP, device_map=SBVITS2_DEVICE)
        bert_models.load_tokenizer(Languages.JP)
        print(f"✓ BERT Model pre-loaded in {time.time()-start:.2f}s")

        # Step 3: Warm-up
        print("\n[Step 3/3] Warm-up inference...")
        start = time.time()
        _ = tts_model_sbvits2.infer(text="システム起動", language=Languages.JP, speaker_id=0)
        print(f"✓ Warm-up completed in {time.time()-start:.2f}s")

        tts_bert_ready = True

        print("\n" + "=" * 70)
        print("  ✅ Style-Bert-VITS2 Ready! (0.1秒未満)")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"[TTS-BERT ERROR] Failed to initialize: {e}")
        import traceback
        traceback.print_exc()


def initialize_fish():
    """Initialize Fish Speech TTS configuration"""
    global fish_config, tts_fish_ready

    if not FISH_CONFIG_PATH.exists():
        print(f"[TTS-FISH ERROR] Config not found: {FISH_CONFIG_PATH}")
        return

    try:
        with open(FISH_CONFIG_PATH, 'r', encoding='utf-8') as f:
            fish_config = yaml.safe_load(f)

        print("[TTS-FISH] Configuration loaded")
        print(f"  Model: {fish_config['model']['name']}")
        print(f"  Temperature: {fish_config['generation']['temperature']}")
        print(f"  Reference: {fish_config['reference']['sample_count']} samples")

        tts_fish_ready = True

    except Exception as e:
        print(f"[TTS-FISH ERROR] Failed to load config: {e}")


def generate_botan_response(user_message: str) -> str:
    """Generate Botan's response using Ollama LLM"""
    global global_chat_history

    global_chat_history.append({"role": "user", "content": user_message})

    try:
        start = time.time()

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": global_chat_history,
                "stream": False,
                "options": {"temperature": OLLAMA_TEMPERATURE}
            },
            timeout=60
        )

        llm_time = time.time() - start

        if response.status_code == 200:
            result = response.json()
            botan_reply = result.get("message", {}).get("content", "")

            global_chat_history.append({"role": "assistant", "content": botan_reply})
            save_chat_history()

            print(f"[LLM] Generated in {llm_time:.3f}s: '{botan_reply[:50]}...'")
            return botan_reply.strip()
        else:
            print(f"[LLM ERROR] Ollama returned status {response.status_code}")
            return "あれ〜？ちょっと調子悪いかも...ごめんね！"

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "え〜、なんか固まっちゃった...ごめん！"


def generate_sbvits2_audio(text: str) -> Tuple[bytes, str]:
    """Generate audio using Style-Bert-VITS2"""
    global tts_model_sbvits2

    if tts_model_sbvits2 is None:
        print("[TTS-BERT ERROR] Model not initialized")
        return b"", ""

    try:
        start = time.time()

        sr, audio = tts_model_sbvits2.infer(
            text=text,
            language=Languages.JP,
            speaker_id=0,
            style="Neutral",
            style_weight=1.0,
            sdp_ratio=0.2,
            length=1.0,
        )

        elapsed = time.time() - start
        print(f"[TTS-BERT] Generated in {elapsed:.3f}s")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"botan_bert_{timestamp}.wav"

        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sr, audio)
        wav_bytes = wav_buffer.getvalue()

        output_path = AUDIO_OUTPUT_DIR / filename
        with open(output_path, "wb") as f:
            f.write(wav_bytes)

        print(f"[TTS-BERT] Saved: {output_path}")

        return wav_bytes, filename

    except Exception as e:
        print(f"[TTS-BERT ERROR] {e}")
        return b"", ""


def generate_fish_audio(text: str) -> Tuple[bytes, str]:
    """Generate audio using Fish Speech"""
    if fish_config is None:
        print("[TTS-FISH ERROR] Config not loaded")
        return b"", ""

    try:
        start = time.time()
        print(f"[TTS-FISH] Starting generation...")

        # Use botan_tts.py wrapper
        cmd = [
            str(FISH_VENV_PYTHON),
            str(FISH_BASE_PATH / "botan_tts.py"),
            "--text", text,
            "--output", str(AUDIO_OUTPUT_DIR / "temp_fish.wav")
        ]

        result = subprocess.run(
            cmd,
            cwd=str(FISH_BASE_PATH),
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )

        elapsed = time.time() - start
        print(f"[TTS-FISH] Generated in {elapsed:.1f}s")

        # Read generated audio
        temp_wav = AUDIO_OUTPUT_DIR / "temp_fish.wav"
        if not temp_wav.exists():
            print("[TTS-FISH ERROR] Output file not found")
            return b"", ""

        with open(temp_wav, 'rb') as f:
            wav_bytes = f.read()

        # Rename to timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"botan_fish_{timestamp}.wav"
        final_path = AUDIO_OUTPUT_DIR / filename

        temp_wav.rename(final_path)
        print(f"[TTS-FISH] Saved: {final_path}")

        return wav_bytes, filename

    except subprocess.TimeoutExpired:
        print("[TTS-FISH ERROR] Generation timeout")
        return b"", ""
    except Exception as e:
        print(f"[TTS-FISH ERROR] {e}")
        import traceback
        traceback.print_exc()
        return b"", ""


# Initialize FastAPI app
app = FastAPI(title="Unified TTS Server - Bert + Fish")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "llm_ready": llm_ready,
        "tts_bert_ready": tts_bert_ready,
        "tts_fish_ready": tts_fish_ready,
        "status": "ready" if llm_ready else "initializing"
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return botan_config


@app.post("/api/config")
async def update_config(config: dict):
    """Update configuration"""
    global botan_config

    try:
        botan_config["user_info"] = config.get("user_info", "")
        botan_config["aite_info"] = config.get("aite_info", "")

        save_config()

        # Update system prompt in chat history
        system_prompt = generate_system_prompt()
        if global_chat_history and global_chat_history[0].get("role") == "system":
            global_chat_history[0]["content"] = system_prompt
            save_chat_history()
            print("[CONFIG] System prompt updated in chat history")

        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        print(f"[CONFIG ERROR] Failed to update: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def get():
    """Serve HTML interface"""
    html_path = Path("unified_webui.html")
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(html_content)
    else:
        return HTMLResponse("<h1>Error: unified_webui.html not found</h1>", status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEBSOCKET] Client connected")

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                user_message = data["content"]
                voice_enabled = data.get("voice_enabled", True)
                tts_engine = data.get("tts_engine", "bert")  # "bert" or "fish"

                print(f"[WEBSOCKET] User: {user_message}, Voice: {voice_enabled}, Engine: {tts_engine}")

                # Generate Botan's response using LLM
                loop = asyncio.get_event_loop()
                botan_response = await loop.run_in_executor(
                    None,
                    generate_botan_response,
                    user_message
                )

                print(f"[LLM] Botan: {botan_response}")

                # Send text response first
                await websocket.send_json({
                    "type": "text",
                    "content": botan_response
                })

                # Generate and send audio if voice is enabled
                if voice_enabled:
                    if tts_engine == "bert":
                        if not tts_bert_ready:
                            await websocket.send_json({
                                "type": "warning",
                                "message": "Bert TTS初期化中です"
                            })
                        else:
                            audio_data, filename = await loop.run_in_executor(
                                None,
                                generate_sbvits2_audio,
                                botan_response
                            )

                            if audio_data:
                                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": audio_base64,
                                    "filename": filename,
                                    "engine": "bert"
                                })
                                print(f"[TTS-BERT] Audio sent: {filename}")

                    elif tts_engine == "fish":
                        if not tts_fish_ready:
                            await websocket.send_json({
                                "type": "warning",
                                "message": "Fish TTS設定未完了です"
                            })
                        else:
                            audio_data, filename = await loop.run_in_executor(
                                None,
                                generate_fish_audio,
                                botan_response
                            )

                            if audio_data:
                                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": audio_base64,
                                    "filename": filename,
                                    "engine": "fish"
                                })
                                print(f"[TTS-FISH] Audio sent: {filename}")

    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    import threading

    # Load configuration FIRST
    load_config()

    # Load chat history SECOND
    load_chat_history()

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888

    print(f"\n{'='*70}")
    print("Starting Unified TTS Server (Bert + Fish)")
    print(f"Access at: http://localhost:{port}")
    print(f"Memory: {len(global_chat_history)} messages loaded")
    print(f"LLM: Ready (Ollama)")
    print(f"TTS Bert: Initializing in background...")
    print(f"TTS Fish: Initializing in background...")
    print("="*70 + "\n")

    # Initialize both TTS engines in background threads
    bert_thread = threading.Thread(target=initialize_sbvits2, daemon=True)
    fish_thread = threading.Thread(target=initialize_fish, daemon=True)

    bert_thread.start()
    fish_thread.start()

    # Start server immediately
    uvicorn.run(app, host="0.0.0.0", port=port)
