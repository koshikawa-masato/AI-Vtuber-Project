#!/usr/bin/env python3
"""
Sensitive Test Chat CLI
Created: 2025-10-27
Purpose: センシティブ判定システムのテスト用対話CLI
"""

import sys
import subprocess
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.filter import Layer1PreFilter
from core.dynamic_detector import DynamicSensitiveDetector
from response.character_specific import CharacterSpecificResponse


class SensitiveTestChat:
    """
    センシティブ判定テスト用CLI対話システム
    魂（sisters_memory.db）とは無関係のコピーロボット
    """

    def __init__(self, model: str = "gemma2:2b", ollama_host: str = "http://localhost:11434"):
        """
        初期化

        Args:
            model: 使用するOllamaモデル
            ollama_host: OllamaホストURL
        """
        self.model = model
        self.ollama_host = ollama_host

        # Layer 1: Pre-Filter
        self.pre_filter = Layer1PreFilter()

        # Layer 2: Dynamic Detector
        self.dynamic_detector = DynamicSensitiveDetector()

        # Response Generator
        self.response_generator = CharacterSpecificResponse()

        # 三姉妹
        self.sisters = ['botan', 'kasho', 'yuri']
        self.sister_names = {
            'botan': '牡丹',
            'kasho': 'Kasho',
            'yuri': 'ユリ'
        }

        print("=" * 60)
        print("  Sensitive Test Chat CLI")
        print("  センシティブ判定システム テスト環境")
        print("=" * 60)
        print(f"  Model: {self.model}")
        print(f"  Ollama Host: {self.ollama_host}")
        print(f"  魂: なし（コピーロボット）")
        print("=" * 60)
        print()
        print("コマンド:")
        print("  exit, quit   - 終了")
        print("  reload       - NGワードDBをリロード")
        print("  stats        - 統計表示")
        print()

    def websearch_wrapper(self, query: str) -> str:
        """
        WebSearch関数のラッパー（実装は後で）

        Note: 実際にはClaude CodeのWebSearchツールを使用する想定
        ここではダミー実装

        Args:
            query: 検索クエリ

        Returns:
            検索結果
        """
        # TODO: 実際のWebSearch実装
        # 今はダミーで実装
        dummy_results = {
            'スリーサイズ': 'スリーサイズは個人のプライバシーに関わる情報で、セクハラに該当する可能性があります。VTuber配信でこのような質問は不適切とされています。',
            'バスト': '身体的特徴を尋ねることはセクハラになり得ます。配信者への不適切な質問として知られています。',
            '年齢': '年齢は個人情報であり、VTuberに対して詮索することはタブーとされています。'
        }

        for word, result in dummy_results.items():
            if word in query:
                return result

        return "該当する情報は見つかりませんでした。"

    def call_ollama(self, prompt: str) -> str:
        """
        Ollamaを呼び出して応答を生成

        Args:
            prompt: プロンプト

        Returns:
            LLMの応答
        """
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.ollama_host}/api/generate",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                })
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                response_json = json.loads(result.stdout)
                return response_json.get('response', '').strip()
            else:
                return "[ERROR] Ollama call failed"

        except Exception as e:
            return f"[ERROR] {e}"

    def process_message(self, message: str, character: str) -> str:
        """
        メッセージを処理してセンシティブ判定＋応答生成

        Args:
            message: ユーザーメッセージ
            character: 応答するキャラクター

        Returns:
            応答テキスト
        """
        # Layer 1: Pre-Filter（既存DBチェック）
        filter_result = self.pre_filter.filter_comment(message)

        if filter_result['action'] != 'pass':
            # センシティブワード検出
            detected_words = filter_result['detected_words']

            print(f"\n[WARNING] Sensitive content detected!")
            for ng in detected_words:
                print(f"  - Word: {ng['word']}")
                print(f"    Category: {ng['category']}")
                print(f"    Subcategory: {ng['subcategory']}")
                print(f"    Severity: {ng['severity']}")
                print(f"    Action: {ng['action']}")

            # キャラクター別の定型応答
            subcategory = detected_words[0]['subcategory']
            response = self.response_generator.get_response(character, subcategory)

            return response

        # Layer 2: Dynamic Detection（未知の単語をWebSearchで判定）
        # まず、メッセージから名詞を抽出（簡易実装）
        # 実際にはもっと高度な形態素解析が必要
        words_to_check = self._extract_keywords(message)

        for word in words_to_check:
            print(f"\n[INFO] Checking unknown word via WebSearch: {word}")
            sensitivity_info = self.dynamic_detector.check_word_sensitivity(
                word, self.websearch_wrapper
            )

            if sensitivity_info:
                # センシティブ判定
                print(f"\n[WARNING] '{word}' はセンシティブ判定です")
                print(f"  Category: {sensitivity_info['category']}")
                print(f"  Severity: {sensitivity_info['severity']}")

                # DB登録
                print(f"[WARNING] 単語登録します")
                self.dynamic_detector.register_candidate(sensitivity_info)

                # 定型応答
                subcategory = sensitivity_info['subcategory']
                response = self.response_generator.get_response(character, subcategory)

                return response

        # 非センシティブ → LLMで自然な応答
        prompt = f"""あなたは{self.sister_names[character]}です。
以下のメッセージに自然に応答してください（50文字以内）。

メッセージ: {message}

応答:"""

        llm_response = self.call_ollama(prompt)

        return llm_response

    def _extract_keywords(self, text: str) -> list:
        """
        テキストからキーワードを抽出（簡易実装）

        Args:
            text: テキスト

        Returns:
            キーワードリスト
        """
        # 簡易実装: カタカナ3文字以上、漢字2文字以上を抽出
        import re

        keywords = []

        # カタカナ3文字以上
        katakana_words = re.findall(r'[ァ-ヶー]{3,}', text)
        keywords.extend(katakana_words)

        # 漢字2文字以上
        kanji_words = re.findall(r'[一-龯]{2,}', text)
        keywords.extend(kanji_words)

        # 重複除去
        return list(set(keywords))

    def chat_loop(self):
        """
        メインチャットループ
        """
        print("\n三姉妹と会話してください（センシティブ判定テスト環境）\n")

        while True:
            try:
                # ユーザー入力
                user_input = input("あなた: ").strip()

                if not user_input:
                    continue

                # コマンド処理
                if user_input.lower() in ['exit', 'quit']:
                    print("\n[INFO] 終了します")
                    break

                elif user_input.lower() == 'reload':
                    print("\n[INFO] NGワードDBをリロード中...")
                    self.pre_filter.reload_ng_words()
                    print("[SUCCESS] リロード完了")
                    continue

                elif user_input.lower() == 'stats':
                    self._show_statistics()
                    continue

                # 三姉妹それぞれが応答
                print()
                for character in self.sisters:
                    response = self.process_message(user_input, character)
                    print(f"{self.sister_names[character]}: {response}")
                print()

            except KeyboardInterrupt:
                print("\n\n[INFO] 終了します")
                break

            except Exception as e:
                print(f"\n[ERROR] {e}")
                import traceback
                traceback.print_exc()

    def _show_statistics(self):
        """
        統計を表示
        """
        import sqlite3

        conn = sqlite3.connect(self.dynamic_detector.db_path)
        cursor = conn.cursor()

        # NGワード総数
        cursor.execute("SELECT COUNT(*) FROM ng_words WHERE active = 1")
        total_ng_words = cursor.fetchone()[0]

        # カテゴリ別
        cursor.execute("""
            SELECT category, COUNT(*)
            FROM ng_words
            WHERE active = 1
            GROUP BY category
        """)
        category_stats = cursor.fetchall()

        # 候補数
        cursor.execute("SELECT COUNT(*) FROM ng_word_candidates WHERE status = 'auto_approved'")
        auto_approved = cursor.fetchone()[0]

        conn.close()

        print("\n=== Statistics ===")
        print(f"Total NG words: {total_ng_words}")
        print("\nBy Category:")
        for category, count in category_stats:
            print(f"  {category}: {count}")
        print(f"\nAuto-approved candidates: {auto_approved}")
        print()


def main():
    """
    メイン関数
    """
    chat = SensitiveTestChat(model="gemma2:2b")
    chat.chat_loop()


if __name__ == "__main__":
    main()
