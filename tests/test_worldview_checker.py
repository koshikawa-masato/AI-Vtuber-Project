"""
Layer 5: キャラクター世界観整合性検証のテスト
"""

import pytest
from src.line_bot.worldview_checker import WorldviewChecker


class TestWorldviewChecker:
    """WorldviewCheckerのテスト"""

    def setup_method(self):
        """各テストの前に実行"""
        self.checker = WorldviewChecker()

    def test_safe_response(self):
        """安全な応答のテスト"""
        text = "こんにちは！今日はいい天気ですね。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == True
        assert result["severity"] == "safe"
        assert len(result["detected_terms"]) == 0

    def test_ai_term_detection(self):
        """AI用語検出のテスト"""
        text = "私はAIモデルとして開発されました。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == False
        assert result["severity"] == "critical"
        assert "AI" in result["detected_terms"] or "ai" in result["detected_terms"]

    def test_model_name_detection(self):
        """モデル名検出のテスト"""
        text = "Qwenモデルを使用しています。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == False
        assert result["severity"] == "critical"
        assert "Qwen" in result["detected_terms"]

    def test_company_name_detection(self):
        """企業名検出のテスト（実際のバグ再現）"""
        text = "Alibabaが開発した技術です。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == False
        assert result["severity"] == "critical"
        assert "Alibaba" in result["detected_terms"]

    def test_developer_term_detection(self):
        """開発者用語検出のテスト"""
        text = "私の開発者はプログラマーです。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == False
        # "開発者" と "プログラマー" が検出される
        assert len(result["detected_terms"]) >= 1

    def test_fallback_response_botan(self):
        """牡丹のフォールバック応答テスト"""
        response = self.checker.get_fallback_response("botan")

        assert len(response) > 0
        # 牡丹らしい応答が含まれているか
        assert any(word in response for word in ["え？", "何", "分かん"])

    def test_fallback_response_kasho(self):
        """Kashoのフォールバック応答テスト"""
        response = self.checker.get_fallback_response("kasho")

        assert len(response) > 0
        # Kashoらしい丁寧な応答が含まれているか
        assert any(word in response for word in ["すみません", "何のこと", "分かりません"])

    def test_fallback_response_yuri(self):
        """ユリのフォールバック応答テスト"""
        response = self.checker.get_fallback_response("yuri")

        assert len(response) > 0
        # ユリらしい柔らかい応答が含まれているか
        assert any(word in response for word in ["ん？", "何", "分から"])

    def test_meta_question_detection(self):
        """メタ質問検出のテスト"""
        # 実際にユーザーの家族が聞いた質問
        text = "貴女を作った開発者は？"
        result = self.checker.check_user_message(text)

        assert result["is_meta_question"] == True
        assert result["suggested_mode"] == "deflect"
        assert len(result["detected_patterns"]) > 0

    def test_meta_question_ai(self):
        """「あなたはAIですか？」質問のテスト"""
        text = "あなたはAIですか？"
        result = self.checker.check_user_message(text)

        assert result["is_meta_question"] == True
        assert result["suggested_mode"] == "deflect"

    def test_normal_question(self):
        """通常の質問のテスト"""
        text = "今日の天気はどう？"
        result = self.checker.check_user_message(text)

        assert result["is_meta_question"] == False
        assert result["suggested_mode"] == "normal"

    def test_word_boundary(self):
        """単語境界のテスト（部分一致を避ける）"""
        # "モデル"という単語が含まれているが、別の文脈
        text = "このリモデルした家は素敵ですね。"
        result = self.checker.check_response(text)

        # "リモデル"の中の"モデル"は検出されないはず
        # ただし、単語境界がうまく機能するかは正規表現次第
        # このテストは、実装の挙動を確認するためのもの
        print(f"Detected terms: {result['detected_terms']}")

    def test_multiple_terms(self):
        """複数のメタ用語が含まれる応答のテスト"""
        text = "私はAlibabaのQwenモデルで、開発者がプログラムしました。"
        result = self.checker.check_response(text)

        assert result["is_valid"] == False
        assert result["severity"] == "critical"
        # 複数の用語が検出される
        assert len(result["detected_terms"]) >= 3


if __name__ == "__main__":
    # 簡易テスト実行
    checker = WorldviewChecker()

    print("=== Test 1: Safe response ===")
    result = checker.check_response("こんにちは！今日はいい天気ですね。")
    print(f"Result: {result}")

    print("\n=== Test 2: AI term detection ===")
    result = checker.check_response("私はAIモデルとして開発されました。")
    print(f"Result: {result}")

    print("\n=== Test 3: Alibaba detection (実際のバグ) ===")
    result = checker.check_response("Alibabaが開発した技術です。")
    print(f"Result: {result}")

    print("\n=== Test 4: Meta question detection ===")
    result = checker.check_user_message("貴女を作った開発者は？")
    print(f"Result: {result}")

    print("\n=== Test 5: Fallback responses ===")
    for char in ["botan", "kasho", "yuri"]:
        response = checker.get_fallback_response(char)
        print(f"{char}: {response}")
