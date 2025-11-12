#!/usr/bin/env python3
"""
Copy Robot Interactive Chat CLI
Created: 2025-10-27
Purpose: Copy RobotのDBを使って三姉妹と会話し、記憶と学習語彙を確認
"""

import sys
import sqlite3
import subprocess
import json
import os
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# Add parent directory to path
# Get absolute path of this script
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
# Insert sensitive_system first, then youtube_learning_system
sys.path.insert(0, str(project_root / "youtube_learning_system"))
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(project_root))

# Debug: Print sys.path
if os.getenv('DEBUG'):
    print(f"[DEBUG] script_dir: {script_dir}")
    print(f"[DEBUG] sys.path: {sys.path[:3]}")

try:
    from core.filter import Layer1PreFilter
    from response.character_specific import CharacterSpecificResponse
    from conversation import InterestAnalyzer
    from src.line_bot.worldview_checker import WorldviewChecker
    from src.core.prompt_manager import PromptManager
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print(f"[ERROR] Current directory: {os.getcwd()}")
    print(f"[ERROR] Script directory: {script_dir}")
    print(f"[ERROR] sys.path[0]: {sys.path[0]}")
    print("\n[FIX] Please run from the sensitive_system directory:")
    print(f"  cd {script_dir}")
    print(f"  python3 {Path(__file__).name} <args>")
    sys.exit(1)


class CopyRobotMemoryLoader:
    """
    Copy RobotのDBから記憶を読み込む
    """

    def __init__(self, copy_robot_db_path: str):
        """
        初期化

        Args:
            copy_robot_db_path: Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db
        """
        self.db_path = copy_robot_db_path

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """
        最近のイベントを取得

        Args:
            limit: 取得件数

        Returns:
            イベントリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT event_id, event_number, event_name, event_date, description
            FROM sister_shared_events
            ORDER BY event_number DESC
            LIMIT ?
        """, (limit,))

        events = []
        for row in cursor.fetchall():
            events.append({
                'event_id': row[0],
                'event_number': row[1],
                'event_name': row[2],
                'event_date': row[3],
                'description': row[4]
            })

        conn.close()
        return events

    def get_character_recent_memories(self, character: str, limit: int = 5) -> List[Dict]:
        """
        キャラクターの最近の記憶を取得

        Args:
            character: 'botan', 'kasho', or 'yuri'
            limit: 取得件数

        Returns:
            記憶リスト
        """
        table_name = f"{character}_memories"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT memory_id, event_id, memory_date, diary_entry,
                       {character}_emotion, {character}_thought
                FROM {table_name}
                ORDER BY memory_date DESC
                LIMIT ?
            """, (limit,))

            memories = []
            for row in cursor.fetchall():
                memories.append({
                    'memory_id': row[0],
                    'event_id': row[1],
                    'memory_date': row[2],
                    'diary_entry': row[3],
                    'emotion': row[4],
                    'thought': row[5]
                })

            conn.close()
            return memories

        except sqlite3.OperationalError:
            conn.close()
            return []

    def search_memories_by_keyword(self, character: str, keyword: str, limit: int = 5) -> List[Dict]:
        """
        キーワードで記憶を検索

        Args:
            character: 'botan', 'kasho', or 'yuri'
            keyword: 検索キーワード
            limit: 取得件数

        Returns:
            記憶リスト
        """
        table_name = f"{character}_memories"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT memory_id, event_id, memory_date, diary_entry,
                       {character}_emotion, {character}_thought
                FROM {table_name}
                WHERE diary_entry LIKE ? OR {character}_thought LIKE ?
                ORDER BY memory_date DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))

            memories = []
            for row in cursor.fetchall():
                memories.append({
                    'memory_id': row[0],
                    'event_id': row[1],
                    'memory_date': row[2],
                    'diary_entry': row[3],
                    'emotion': row[4],
                    'thought': row[5]
                })

            conn.close()
            return memories

        except sqlite3.OperationalError:
            conn.close()
            return []


class VocabularyLoader:
    """
    YouTube学習システムから語彙を読み込む
    """

    def __init__(self, youtube_learning_db_path: str = None):
        """
        初期化

        Args:
            youtube_learning_db_path: Path to youtube_learning.db
        """
        if youtube_learning_db_path is None:
            youtube_learning_db_path = "/home/koshikawa/toExecUnit/youtube_learning_system/database/youtube_learning.db"

        self.db_path = youtube_learning_db_path

    def get_learned_vocabulary(self, character: str) -> List[Dict]:
        """
        学習済み語彙を取得

        Args:
            character: 'botan', 'kasho', or 'yuri'

        Returns:
            語彙リスト
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT w.word, w.meaning, w.etymology, w.usage_example,
                       w.category, w.language, w.translation
                FROM word_knowledge w
                LEFT JOIN word_sensitivity s ON w.word_id = s.word_id
                WHERE w.learned_by = ? AND (s.level = 'safe' OR s.level IS NULL)
                ORDER BY w.first_seen_at DESC
            """, (character,))

            vocabulary = []
            for row in cursor.fetchall():
                vocabulary.append({
                    'word': row[0],
                    'meaning': row[1],
                    'etymology': row[2],
                    'usage_example': row[3],
                    'category': row[4],
                    'language': row[5],
                    'translation': row[6]
                })

            conn.close()
            return vocabulary

        except Exception as e:
            print(f"[ERROR] Failed to load vocabulary: {e}")
            return []

    def format_vocabulary_for_prompt(self, character: str) -> str:
        """
        プロンプト用に語彙をフォーマット

        Args:
            character: 'botan', 'kasho', or 'yuri'

        Returns:
            フォーマット済み語彙文字列
        """
        vocabulary = self.get_learned_vocabulary(character)

        if not vocabulary:
            return ""

        lines = ["\n【あなたが学習した語彙】\n"]

        for vocab in vocabulary[:10]:  # 最初の10語
            word = vocab['word']
            meaning = vocab['meaning'] or '(意味不明)'

            if vocab['language'] == 'en' and vocab['translation']:
                lines.append(f"- {word} ({vocab['translation']}): {meaning[:80]}")
            else:
                lines.append(f"- {word}: {meaning[:80]}")

        lines.append("\nこれらの語彙を理解して、適切に使用してください。")

        return '\n'.join(lines)


class CopyRobotChat:
    """
    Copy Robot Interactive Chat System
    """

    def __init__(self,
                 copy_robot_db_path: str,
                 model: str = "gemma2:2b",
                 ollama_host: str = "http://localhost:11434"):
        """
        初期化

        Args:
            copy_robot_db_path: Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db
            model: Ollamaモデル名
            ollama_host: OllamaホストURL
        """
        self.copy_robot_db = copy_robot_db_path
        self.model = model
        self.ollama_host = ollama_host

        # Memory Loader
        self.memory_loader = CopyRobotMemoryLoader(copy_robot_db_path)

        # Vocabulary Loader
        self.vocab_loader = VocabularyLoader()

        # Sensitive Filter
        self.pre_filter = Layer1PreFilter()
        self.response_generator = CharacterSpecificResponse()

        # Characters
        self.sisters = ['botan', 'kasho', 'yuri']
        self.sister_names = {
            'botan': '牡丹',
            'kasho': 'Kasho',
            'yuri': 'ユリ'
        }

        # Console
        self.console = Console()

        # Conversation history (per character)
        self.history = {
            'botan': [],
            'kasho': [],
            'yuri': []
        }

        # Interest-based conversation system (Phase 1)
        self.interest_analyzer = InterestAnalyzer()
        self.last_responder = None  # Track last responder for context continuation

        # Layer 5: WorldviewChecker
        self.worldview_checker = WorldviewChecker()
        self.console.print("[green]✓ Layer 5: WorldviewChecker初期化完了[/green]")

        # 統一プロンプト管理システム
        self.prompt_manager = PromptManager()
        self.console.print("[green]✓ 統一PromptManager初期化完了[/green]")

        # Setup chat log file
        self.log_file = None
        self._setup_log_file()

        self._show_welcome()
        self._check_ollama_model()

    def _show_welcome(self):
        """
        ウェルカムメッセージ表示
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Copy Robot Interactive Chat[/bold cyan]\n"
            "コピーロボットとの対話システム",
            border_style="cyan"
        ))
        self.console.print()
        self.console.print(f"[cyan]Copy Robot DB: {self.copy_robot_db}")
        self.console.print(f"[cyan]Model: {self.model}")
        self.console.print()

    def _check_ollama_model(self):
        """
        Ollamaモデルが利用可能かチェック（自動ダウンロード対応）
        """
        try:
            # Check if Ollama is running
            result = subprocess.run(
                ["curl", "-s", f"{self.ollama_host}/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                self.console.print("[red]⚠️  警告: Ollamaに接続できません[/red]")
                self.console.print(f"[yellow]Ollamaが起動しているか確認してください: {self.ollama_host}[/yellow]")
                self.console.print()
                return

            # Parse available models
            try:
                models_json = json.loads(result.stdout)
                available_models = [m['name'] for m in models_json.get('models', [])]

                # Check if specified model is available
                if self.model not in available_models:
                    self.console.print(f"[yellow]⚠️  モデル '{self.model}' が見つかりません[/yellow]")

                    if available_models:
                        self.console.print("[cyan]利用可能なモデル:")
                        for model in available_models[:5]:  # Show first 5
                            self.console.print(f"  - {model}")
                        if len(available_models) > 5:
                            self.console.print(f"  ... and {len(available_models) - 5} more")
                        self.console.print()

                    # Auto-download prompt
                    self.console.print(f"[bold cyan]モデル '{self.model}' を自動ダウンロードしますか？[/bold cyan]")
                    self.console.print("[dim]（10GbE環境では数分でダウンロードできます）[/dim]")

                    try:
                        choice = self.console.input("[bold green]ダウンロードする (Y/n):[/bold green] ").strip().lower()

                        if choice in ['', 'y', 'yes']:
                            # Download model
                            if self._download_model(self.model):
                                self.console.print(f"✓ モデル '{self.model}' のダウンロードが完了しました")
                                self.console.print()
                            else:
                                self.console.print(f"[red]✗ モデル '{self.model}' のダウンロードに失敗しました[/red]")
                                self.console.print("[yellow]手動でダウンロードしてください: ollama pull {self.model}[/yellow]")
                                self.console.print()
                                sys.exit(1)
                        else:
                            self.console.print("[yellow]ダウンロードをキャンセルしました[/yellow]")
                            self.console.print()
                            sys.exit(0)

                    except KeyboardInterrupt:
                        self.console.print("\n[yellow]キャンセルされました[/yellow]")
                        sys.exit(0)
                else:
                    self.console.print(f"✓ モデル '{self.model}' が利用可能です")
                    self.console.print()

            except json.JSONDecodeError:
                self.console.print("[yellow]⚠️  警告: Ollamaの応答を解析できませんでした[/yellow]")
                self.console.print()

        except subprocess.TimeoutExpired:
            self.console.print("[red]⚠️  警告: Ollamaへの接続がタイムアウトしました[/red]")
            self.console.print()
        except Exception as e:
            self.console.print(f"[yellow]⚠️  警告: Ollamaチェック中にエラー: {e}[/yellow]")
            self.console.print()

    def _download_model(self, model: str) -> bool:
        """
        Ollamaモデルをダウンロード

        Args:
            model: モデル名

        Returns:
            成功: True, 失敗: False
        """
        self.console.print()
        self.console.print(f"[bold cyan]モデル '{model}' をダウンロード中...[/bold cyan]")
        self.console.print()

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Downloading {model}...", total=None)

                # Execute ollama pull
                process = subprocess.Popen(
                    ["ollama", "pull", model],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Monitor output
                last_line = ""
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        last_line = line
                        # Update progress description with latest output
                        progress.update(task, description=f"[cyan]{line[:60]}...")

                process.wait()

                if process.returncode == 0:
                    progress.update(task, description=f"✓ Download complete: {model}")
                    return True
                else:
                    progress.update(task, description=f"[red]✗ Download failed: {last_line}[/red]")
                    return False

        except FileNotFoundError:
            self.console.print("[red]✗ 'ollama' コマンドが見つかりません[/red]")
            self.console.print("[yellow]Ollamaがインストールされているか確認してください[/yellow]")
            return False

        except Exception as e:
            self.console.print(f"[red]✗ ダウンロード中にエラーが発生: {e}[/red]")
            return False

    def _setup_log_file(self):
        """
        Setup chat log file in logs/ directory
        Filename format: chatlog_YYYYMMDDHHMMSS.log
        """
        # Create logs directory if not exists
        logs_dir = Path(__file__).parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        log_filename = f"chatlog_{timestamp}.log"
        self.log_file = logs_dir / log_filename

        # Write initial header
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"Copy Robot Chat Log\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {self.model}\n")
            f.write(f"Database: {self.copy_robot_db}\n")
            f.write("=" * 60 + "\n\n")

        self.console.print(f"Chat log: {self.log_file}")
        self.console.print()

    def _log_message(self, speaker: str, message: str):
        """
        Log message to chat log file

        Args:
            speaker: Speaker name (e.g., "User", "牡丹", "Kasho", "ユリ", "System")
            message: Message content
        """
        if not self.log_file:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {speaker}: {message}\n")
        except Exception as e:
            # Fail silently to avoid disrupting chat
            pass

    def generate_system_prompt(self, character: str, recent_context: bool = True) -> str:
        """
        システムプロンプトを生成（語彙統合）

        Template file (shared with production) + dynamic content:
        1. 基本性格プロンプト（テンプレートから）
        2. 記憶セクション（動的生成）
        3. 語彙セクション（動的生成）

        Args:
            character: 'botan', 'kasho', or 'yuri'
            recent_context: 最近の記憶を含めるか

        Returns:
            システムプロンプト
        """
        # 統一プロンプト管理システムから取得
        base_prompt = self.prompt_manager.get_combined_prompt(character)

        # Build memory section
        memory_section = ""
        if recent_context:
            memories = self.memory_loader.get_character_recent_memories(character, limit=3)
            if memories:
                memory_section = "\n【最近の記憶】\n"
                for memory in memories:
                    if memory['diary_entry']:
                        diary_preview = memory['diary_entry'][:100]
                        if len(memory['diary_entry']) > 100:
                            diary_preview += "..."
                        memory_section += f"- {memory['memory_date']}: {diary_preview}\n"

        # Build vocabulary section
        vocab_section = self.vocab_loader.format_vocabulary_for_prompt(character)
        if not vocab_section:
            vocab_section = ""
        else:
            vocab_section = "\n" + vocab_section

        # Insert memory and vocabulary after 基本情報, before 会話のルール
        # Find insertion point
        rules_marker = "【会話のルール - 最重要】"
        if rules_marker in base_prompt:
            parts = base_prompt.split(rules_marker)
            prompt = parts[0] + memory_section + vocab_section + "\n" + rules_marker + parts[1]
        else:
            # Fallback: append at the end
            prompt = base_prompt + memory_section + vocab_section

        return prompt

    def call_ollama(self, system_prompt: str, character: str = 'botan') -> str:
        """
        Ollamaを呼び出して応答生成（本番環境と同じ方式）

        Args:
            system_prompt: システムプロンプト
            character: キャラクター名（パラメータ調整用、会話履歴参照）

        Returns:
            LLM応答
        """
        # Character-specific LLM parameters (from production)
        llm_params = {
            'botan': {
                "temperature": 0.5,
                "num_predict": 1000,  # Increased from 200 to allow complete explanations
                "top_p": 0.85,
                "repeat_penalty": 1.25,
                "stop": ["あなた:", "オジサン:", "User:", "Assistant:"]  # Removed "\n\n" to allow multi-paragraph responses
            },
            'kasho': {
                "temperature": 0.4,  # Lower for more careful responses
                "num_predict": 1000,  # Increased from 250 to allow complete explanations
                "top_p": 0.8,
                "repeat_penalty": 1.2,
                "stop": ["あなた:", "相手:", "User:", "Assistant:"]  # Removed "\n\n" to allow multi-paragraph responses
            },
            'yuri': {
                "temperature": 0.5,  # Balanced for thoughtful responses
                "num_predict": 1000,  # Increased from 200 to allow complete explanations
                "top_p": 0.85,
                "repeat_penalty": 1.15,
                "stop": ["あなた:", "相手:", "User:", "Assistant:"]  # Removed "\n\n" to allow multi-paragraph responses
            }
        }

        try:
            # Start timing
            start_time = time.time()

            # Use /api/chat (like production) instead of /api/generate
            # Include conversation history
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.history[character]

            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.ollama_host}/api/chat",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": llm_params.get(character, llm_params['botan'])
                })
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                try:
                    response_json = json.loads(result.stdout)

                    # Check for errors in response
                    if 'error' in response_json:
                        error_msg = response_json['error']
                        if 'model' in error_msg.lower() and 'not found' in error_msg.lower():
                            return f"[ERROR] Model '{self.model}' not found. Available models: gemma2:2b, qwen2.5:32b, elyza:jp8b"
                        return f"[ERROR] {error_msg}"

                    # Extract message content (chat API format)
                    message = response_json.get('message', {})
                    response = message.get('content', '').strip()

                    if not response:
                        return "[ERROR] Empty response from Ollama"

                    # Filter out "Thinking..." section for gpt-oss models
                    # Format: "Thinking...\n[思考内容]\n...done thinking.\n\n[実際の本文]"
                    if response.startswith('Thinking...'):
                        # Find the end of thinking section
                        thinking_end = response.find('...done thinking.')
                        if thinking_end != -1:
                            # Extract content after thinking section
                            # Skip "...done thinking." and any whitespace
                            response = response[thinking_end + len('...done thinking.'):].strip()

                    # Calculate elapsed time
                    elapsed_time = time.time() - start_time

                    # Append timing to response
                    return f"{response} ({elapsed_time:.3f}s)"

                except json.JSONDecodeError as e:
                    return f"[ERROR] Invalid JSON response: {str(e)[:100]}"
            else:
                stderr = result.stderr[:200] if result.stderr else "No error message"
                return f"[ERROR] Ollama call failed (code {result.returncode}): {stderr}"

        except subprocess.TimeoutExpired:
            return "[ERROR] Ollama request timed out (300s) - 大型モデルの場合、さらに時間が必要な可能性があります"
        except Exception as e:
            return f"[ERROR] {type(e).__name__}: {str(e)[:100]}"

    def process_message(
        self,
        message: str,
        character: str,
        add_greeting_instruction: bool = False
    ) -> str:
        """
        メッセージ処理（センシティブ判定 + LLM応答）

        Args:
            message: ユーザーメッセージ
            character: 応答するキャラクター
            add_greeting_instruction: True if this is a subsequent greeting (Phase 1.5)

        Returns:
            応答
        """
        # Sensitive check
        filter_result = self.pre_filter.filter_comment(message)

        if filter_result['action'] != 'pass':
            detected_words = filter_result['detected_words']
            subcategory = detected_words[0]['subcategory']
            response = self.response_generator.get_response(character, subcategory)
            return f"[⚠️  センシティブ検出] {response}"

        # Add user message to conversation history
        self.history[character].append({
            "role": "user",
            "content": message
        })

        # Generate system prompt with vocabulary
        system_prompt = self.generate_system_prompt(character)

        # Phase 1.5: Add greeting instruction for subsequent greetings
        if add_greeting_instruction:
            from config import GREETING_PROMPT_INSTRUCTION
            system_prompt += GREETING_PROMPT_INSTRUCTION

        # Call LLM with character-specific parameters (history included)
        response = self.call_ollama(system_prompt, character)

        # Extract response without timing info for Layer 5 check
        # Response format: "text (XX.XXXs)"
        import re
        timing_match = re.search(r'\s+\([\d.]+s\)$', response)
        if timing_match:
            response_without_timing = response[:timing_match.start()]
            timing_info = response[timing_match.start():]
        else:
            response_without_timing = response
            timing_info = ""

        # Layer 5: 世界観整合性チェック
        worldview_check = self.worldview_checker.check_response(response_without_timing)

        if not worldview_check["is_valid"]:
            # メタ用語検出：フォールバック応答に置き換え
            fallback_response = self.worldview_checker.get_fallback_response(character)
            self.console.print(f"[yellow]⚠ Layer 5: 世界観違反検出 - {worldview_check['reason']}[/yellow]")
            self.console.print(f"[yellow]  検出用語: {worldview_check['detected_terms'][:3]}[/yellow]")
            response_without_timing = fallback_response

        # Add assistant response to conversation history
        self.history[character].append({
            "role": "assistant",
            "content": response_without_timing
        })

        # Return with timing info
        return response_without_timing + timing_info

    def _handle_low_interest_case(
        self,
        message: str,
        interest_scores: Dict[str, float]
    ):
        """
        Handle case where all characters have low interest

        Strategy: All characters remain silent (no one is interested)

        Args:
            message: User's message
            interest_scores: Interest scores for all characters
        """
        # All characters remain silent
        self.console.print()
        for character in self.sisters:
            self.console.print(f"[dim]{self.sister_names[character]}: ...[/dim]")

            # Log silence
            self._log_message(self.sister_names[character], "...")

        self.console.print()

        # Clear last_responder (no one is really interested)
        self.last_responder = None

    def _handle_coordinated_greeting(
        self,
        message: str,
        responders: List[str],
        greeting_type: str
    ):
        """
        Handle coordinated greeting with templates (Phase 1.5)

        Used when: topic='greeting' AND is_first_message=True

        Args:
            message: User's message (for history)
            responders: List of interested characters
            greeting_type: Type of greeting ('casual', 'morning', 'night', 'formal')
        """
        self.console.print()

        for character in self.sisters:
            if character in responders:
                # Add user message to conversation history
                self.history[character].append({
                    "role": "user",
                    "content": message
                })

                # Get coordinated greeting template
                greeting_response = self.interest_analyzer.get_coordinated_greeting(
                    character,
                    greeting_type
                )

                # Add assistant response to conversation history
                self.history[character].append({
                    "role": "assistant",
                    "content": greeting_response
                })

                # Display response
                self.console.print(f"[bold]{self.sister_names[character]}:[/bold] {greeting_response}")
                self.console.print()

                # Log greeting response
                self._log_message(self.sister_names[character], greeting_response)
            else:
                # Silence (not interested)
                self.console.print(f"[dim]{self.sister_names[character]}: ...[/dim]")

                # Log silence
                self._log_message(self.sister_names[character], "...")

    def show_character_info(self, character: str):
        """
        キャラクター情報表示（記憶・語彙）

        Args:
            character: 'botan', 'kasho', or 'yuri'
        """
        self.console.print()
        self.console.print(f"[bold cyan]═══ {self.sister_names[character]} の情報 ═══[/bold cyan]")
        self.console.print()

        # Vocabulary
        vocabulary = self.vocab_loader.get_learned_vocabulary(character)
        self.console.print(f"[yellow]学習語彙数:[/yellow] {len(vocabulary)}語")

        if vocabulary:
            table = Table(title="学習済み語彙（最初の10語）", box=box.ROUNDED)
            table.add_column("単語", style="cyan")
            table.add_column("意味", style="white")

            for vocab in vocabulary[:10]:
                word = vocab['word']
                meaning = vocab['meaning'][:50] + '...' if vocab['meaning'] and len(vocab['meaning']) > 50 else vocab['meaning']
                table.add_row(word, meaning or '(意味不明)')

            self.console.print(table)

        # Recent memories
        memories = self.memory_loader.get_character_recent_memories(character, limit=5)
        self.console.print()
        self.console.print(f"[yellow]最近の記憶:[/yellow] {len(memories)}件")

        if memories:
            for memory in memories:
                self.console.print(f"\n[cyan]{memory['memory_date']}")
                if memory['diary_entry']:
                    entry = memory['diary_entry'][:100] + '...' if len(memory['diary_entry']) > 100 else memory['diary_entry']
                    self.console.print(f"  {entry}")

        self.console.print()

    def show_recent_events(self):
        """
        最近のイベントを表示
        """
        events = self.memory_loader.get_recent_events(limit=10)

        table = Table(title="最近のイベント（10件）", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("イベント名", style="yellow")
        table.add_column("日付", style="green")

        for event in events:
            table.add_row(
                str(event['event_number']),
                event['event_name'],
                event['event_date']
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def chat_loop(self):
        """
        メインチャットループ
        """
        self.console.print("[bold]コマンド:[/bold]")
        self.console.print("  exit, quit   - 終了")
        self.console.print("  info <character> - キャラクター情報表示 (例: info botan)")
        self.console.print("  events         - 最近のイベント表示")
        self.console.print("  reset          - 会話履歴をクリア")
        self.console.print("  reset <character> - 特定キャラクターの会話履歴をクリア (例: reset botan)")
        self.console.print("  @<character> <message> - 特定のキャラクターに話しかける (例: @botan こんにちは)")
        self.console.print("  llm:<number>  - LLMモデルを変更 (例: llm:26 または 26)")
        self.console.print("  llm:<number> <status> - モデルをテストしてステータス設定 (例: llm:26 ng, llm:26 ok)")
        self.console.print()
        self.console.print("三姉妹と会話を始めましょう！")
        self.console.print()

        while True:
            try:
                # User input
                user_input = self.console.input("あなた: ").strip()

                if not user_input:
                    continue

                # Commands
                if user_input.lower() in ['exit', 'quit']:
                    self.console.print("\n終了します")
                    break

                elif user_input.lower().startswith('info '):
                    character = user_input[5:].strip().lower()
                    if character in self.sisters:
                        self.show_character_info(character)
                    else:
                        self.console.print(f"[red]エラー: 不明なキャラクター '{character}'[/red]")
                    continue

                elif user_input.lower() == 'events':
                    self.show_recent_events()
                    continue

                elif user_input.lower() == 'reset':
                    # Reset all conversation histories and last responder
                    for char in self.sisters:
                        self.history[char] = []
                    self.last_responder = None
                    self.console.print("✓ 全キャラクターの会話履歴をクリアしました")
                    continue

                elif user_input.lower().startswith('reset '):
                    character = user_input[6:].strip().lower()
                    if character in self.sisters:
                        self.history[character] = []
                        # Clear last_responder if it was this character
                        if self.last_responder == character:
                            self.last_responder = None
                        self.console.print(f"✓ {self.sister_names[character]}の会話履歴をクリアしました")
                    else:
                        self.console.print(f"[red]エラー: 不明なキャラクター '{character}'[/red]")
                    continue

                # @character message
                elif user_input.startswith('@'):
                    parts = user_input[1:].split(' ', 1)
                    if len(parts) == 2:
                        character = parts[0].lower()
                        message = parts[1]

                        if character in self.sisters:
                            self.console.print()  # Add blank line before response

                            # Log user input to specific character
                            self._log_message("User", f"@{character} {message}")

                            response = self.process_message(message, character)
                            self.console.print(f"[bold]{self.sister_names[character]}:[/bold] {response}")
                            self.console.print()  # Add blank line after individual response

                            # Log character response
                            self._log_message(self.sister_names[character], response)

                            # Update last responder for context continuation
                            self.last_responder = character
                        else:
                            self.console.print(f"[red]エラー: 不明なキャラクター '{character}'[/red]")
                    else:
                        self.console.print("[red]エラー: メッセージを入力してください (例: @botan こんにちは)[/red]")
                    continue

                # LLM model change: llm:<number> [status] or just <number>
                # Examples: llm:26, 26, llm:26 ng, llm:26 ok
                elif user_input.lower().startswith('llm:') or user_input.isdigit():
                    try:
                        # Parse input: "llm:28 ng" or "28" or "llm:28"
                        parts = user_input.split()
                        status_flag = None

                        if len(parts) >= 2:
                            # "llm:28 ng" or "28 ng"
                            num_part = parts[0]
                            status_flag = parts[1].upper()
                        else:
                            # "llm:28" or "28"
                            num_part = parts[0]

                        # Extract number
                        if num_part.lower().startswith('llm:'):
                            model_num = int(num_part[4:].strip())
                        else:
                            model_num = int(num_part)

                        # Get model list (all models including NG)
                        models = get_installed_models()
                        if not models:
                            self.console.print("[red]エラー: モデルリストの取得に失敗しました[/red]")
                            continue

                        if model_num < 1 or model_num > len(models):
                            self.console.print(f"[red]エラー: モデル番号は 1-{len(models)} の範囲で指定してください[/red]")
                            continue

                        selected_model = models[model_num - 1]['name']

                        # Handle status update (NG, OK, WARN)
                        if status_flag:
                            if status_flag in ['NG', 'OK', 'WARN', 'WARNING']:
                                status = 'WARN' if status_flag == 'WARNING' else status_flag
                                if update_model_status(selected_model, status):
                                    self.console.print(f"✓ {selected_model} を {status} に設定しました")
                                    self._log_message("System", f"Model status updated: {selected_model} → {status}")
                                else:
                                    self.console.print(f"[red]エラー: ステータス更新に失敗しました[/red]")
                            else:
                                self.console.print(f"[red]エラー: 不明なステータス '{status_flag}' (OK/NG/WARN のみ対応)[/red]")
                        else:
                            # Change model
                            old_model = self.model
                            self.model = selected_model
                            self.console.print(f"✓ モデルを変更しました: {old_model} → {self.model}")
                            self.console.print()

                            # Log model change
                            self._log_message("System", f"Model changed: {old_model} → {self.model}")

                    except ValueError:
                        self.console.print("[red]エラー: 数字を入力してください (例: llm:26, 26, llm:26 ng)[/red]")
                    continue

                # Log user input
                self._log_message("User", user_input)

                # Interest-based response selection (Phase 1 + Phase 1.5)
                # Calculate interest scores
                # Check if this is first user message (all histories empty)
                is_first_message = all(len(self.history[char]) == 0 for char in self.sisters)

                context = {
                    'last_responder': self.last_responder,
                    'is_first_message': is_first_message
                }
                interest_scores = self.interest_analyzer.calculate_interest_scores(
                    user_input,
                    context
                )

                # Detect topics for greeting coordination check
                detected_topics = self.interest_analyzer.detect_topics(user_input)

                # Select responders
                responders = self.interest_analyzer.select_responders(interest_scores)

                # Show analysis summary (optional, for debugging)
                if os.getenv('DEBUG_INTEREST'):
                    summary = self.interest_analyzer.format_analysis_summary(
                        user_input,
                        interest_scores,
                        responders
                    )
                    self.console.print(summary)

                # Check for low interest case
                if not responders:
                    # Low interest: handle gracefully
                    self._handle_low_interest_case(user_input, interest_scores)
                else:
                    # Phase 1.5: Check if coordinated greeting is required
                    is_coordinated_greeting = self.interest_analyzer.is_coordinated_greeting_required(
                        detected_topics,
                        context
                    )

                    if is_coordinated_greeting:
                        # Phase 1.5: Coordinated greeting with templates
                        greeting_type = self.interest_analyzer.detect_greeting_type(user_input)
                        self._handle_coordinated_greeting(user_input, responders, greeting_type)
                    else:
                        # Normal case: selected characters respond
                        # Check if this is a greeting (but not first message)
                        is_subsequent_greeting = 'greeting' in detected_topics and not is_first_message

                        self.console.print()
                        for character in self.sisters:
                            if character in responders:
                                # Interested character responds
                                response = self.process_message(
                                    user_input,
                                    character,
                                    add_greeting_instruction=is_subsequent_greeting
                                )
                                self.console.print(f"[bold]{self.sister_names[character]}:[/bold] {response}")
                                self.console.print()

                                # Log character response
                                self._log_message(self.sister_names[character], response)
                            else:
                                # Silence (not interested)
                                self.console.print(f"[dim]{self.sister_names[character]}: ...[/dim]")

                                # Log silence
                                self._log_message(self.sister_names[character], "...")

                    # Update last_responder for context continuation
                    if len(responders) == 1:
                        # Single responder: enable context continuation
                        self.last_responder = responders[0]
                    else:
                        # Multiple responders: clear context
                        self.last_responder = None

            except KeyboardInterrupt:
                self.console.print("\n\n終了します")
                break

            except Exception as e:
                self.console.print(f"\n[red]エラー: {e}[/red]")
                import traceback
                traceback.print_exc()


def get_installed_models() -> List[Dict[str, str]]:
    """
    Get list of installed Ollama models with status information

    Returns:
        List of dicts with model info: [{'name': 'qwen2.5:3b', 'size': '1.9 GB', 'modified': '2 hours ago', 'status': 'OK'}, ...]
        Status can be: 'OK', 'NG', 'WARN', or '' (empty if not tested)
    """
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return []

        # Parse output
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return []

        # Load model status from llms.csv
        model_status_map = {}
        csv_path = Path(__file__).parent / "llms.csv"
        if csv_path.exists():
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        model_name = row.get('LLM Models', '').strip()
                        status = row.get('OK/NG', '').strip().upper()
                        if model_name:
                            model_status_map[model_name] = status
            except Exception as e:
                # Fail silently if CSV parsing fails
                pass

        models = []
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                model_name = parts[0]
                size = parts[2] + ' ' + parts[3]
                modified = ' '.join(parts[4:])
                status = model_status_map.get(model_name, '')

                models.append({
                    'name': model_name,
                    'size': size,
                    'modified': modified,
                    'status': status
                })

        return models

    except Exception as e:
        print(f"[ERROR] Failed to get installed models: {e}")
        return []


def update_model_status(model_name: str, status: str, notes: str = "") -> bool:
    """
    Update model status in llms.csv

    Args:
        model_name: Model name (e.g., "qwen2.5:3b")
        status: Status ("OK", "NG", "WARN")
        notes: Optional notes

    Returns:
        True if successful, False otherwise
    """
    csv_path = Path(__file__).parent / "llms.csv"
    if not csv_path.exists():
        return False

    try:
        # Read existing CSV
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                model_in_csv = row.get('LLM Models', '').strip()
                if model_in_csv == model_name:
                    # Update this row
                    row['exec'] = '✓'
                    row['OK/NG'] = status.upper()
                    if notes:
                        row['notes'] = notes
                rows.append(row)

        # Write back
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return True

    except Exception as e:
        print(f"[ERROR] Failed to update llms.csv: {e}")
        return False


def select_model_interactive() -> str:
    """
    Interactive model selection UI (Richを使用)

    Returns:
        Selected model name
    """
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt

    console = Console()

    console.print("\n[bold cyan]========================================[/bold cyan]")
    console.print("[bold cyan]  Ollama Model Selection[/bold cyan]")
    console.print("[bold cyan]========================================[/bold cyan]\n")

    # Get installed models
    models = get_installed_models()

    if not models:
        console.print("[red]No models installed. Please run download_all_models.sh first.[/red]")
        sys.exit(1)

    # Create table
    table = Table(title="Installed Models", show_header=True, header_style="bold magenta")
    table.add_column("#", justify="right", width=6)
    table.add_column("Model Name", width=40)
    table.add_column("Size", width=12)
    table.add_column("Modified", width=22)
    table.add_column("Status", width=8)

    for idx, model in enumerate(models, start=1):
        status = model.get('status', '')
        is_ng = (status == 'NG')

        # Apply dim style to NG models
        if is_ng:
            table.add_row(
                f"[dim]{idx}[/dim]",
                f"[dim]{model['name']}[/dim]",
                f"[dim]{model['size']}[/dim]",
                f"[dim]{model['modified']}[/dim]",
                f"[dim]{status}[/dim]"
            )
        else:
            # Color-code status
            status_display = status
            if status == 'OK':
                status_display = f"[green]{status}[/green]"
            elif status == 'WARN':
                status_display = f"[yellow]{status}[/yellow]"

            table.add_row(
                str(idx),
                model['name'],
                model['size'],
                model['modified'],
                status_display
            )

    console.print(table)
    console.print()

    # Recommended models
    console.print("[bold green]Recommended for chat:[/bold green]")
    console.print("  • qwen2.5:3b (lightweight, fast)")
    console.print("  • qwen2.5:7b (balanced)")
    console.print("  • qwen2.5:14b (high quality)")
    console.print("  • elyza:jp8b (Japanese specialized)")
    console.print("  • microai/suzume-llama3 (Japanese chat)")
    console.print()

    # Prompt for selection
    while True:
        try:
            choice = Prompt.ask(
                "[bold yellow]Select model number[/bold yellow]",
                default="1"
            )

            model_idx = int(choice) - 1
            if 0 <= model_idx < len(models):
                selected_model = models[model_idx]['name']
                console.print(f"\n[bold green]✓ Selected: {selected_model}[/bold green]\n")
                return selected_model
            else:
                console.print("[red]Invalid number. Please try again.[/red]")

        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            sys.exit(0)


def main():
    """
    メイン関数
    """
    import argparse

    parser = argparse.ArgumentParser(description="Copy Robot Interactive Chat")
    parser.add_argument(
        'copy_robot_db',
        help='Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db'
    )
    parser.add_argument(
        '--model',
        default=None,  # Changed from 'gemma2:2b' to None
        help='Ollama model name (if not specified, interactive selection)'
    )
    parser.add_argument(
        '--ollama-host',
        default='http://localhost:11434',
        help='Ollama host URL (default: http://localhost:11434)'
    )

    args = parser.parse_args()

    # Verify Copy Robot DB exists
    if not Path(args.copy_robot_db).exists():
        print(f"[ERROR] Copy Robot DB not found: {args.copy_robot_db}")
        sys.exit(1)

    # If model not specified, show interactive selection
    if args.model is None:
        args.model = select_model_interactive()

    # Start chat
    chat = CopyRobotChat(args.copy_robot_db, args.model, args.ollama_host)
    chat.chat_loop()


if __name__ == "__main__":
    main()
