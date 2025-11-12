"""
牡丹プロジェクト統一プロンプトエンジニアリング基盤

このモジュールは、プロジェクト全体（LINE Bot、copy_robot、将来の実装）で
共通のプロンプト管理を提供します。

設計思想:
1. 世界観ルール（worldview_rules.txt）: 三姉妹全員共通
2. キャラクター別プロンプト: 各キャラクターの個性
3. DRY原則: 実装モレを防ぐため、1箇所に集約

使用例:
    from src.core.prompt_manager import PromptManager

    pm = PromptManager()
    kasho_prompt = pm.get_combined_prompt("kasho")
"""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """牡丹プロジェクト統一プロンプト管理システム"""

    # サポートするキャラクター
    SUPPORTED_CHARACTERS = ["botan", "kasho", "yuri"]

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        初期化

        Args:
            prompts_dir: プロンプトディレクトリのパス（省略時は自動検出）
        """
        if prompts_dir is None:
            # プロジェクトルート/prompts を自動検出
            project_root = Path(__file__).parent.parent.parent
            self.prompts_dir = project_root / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"プロンプトディレクトリが見つかりません: {self.prompts_dir}")

        # 世界観ルールを読み込み（全キャラクター共通）
        self.worldview_rules = self._load_worldview_rules()

        # キャラクター別プロンプトをキャッシュ
        self.character_prompts: Dict[str, str] = {}

        logger.info(f"PromptManager初期化完了: {self.prompts_dir}")
        logger.info(f"世界観ルール読み込み完了: {len(self.worldview_rules)} 文字")

    def _load_worldview_rules(self) -> str:
        """
        世界観ルール読み込み（全キャラクター共通）

        Returns:
            世界観ルールのテキスト

        Raises:
            FileNotFoundError: worldview_rules.txt が見つからない場合
        """
        worldview_file = self.prompts_dir / "worldview_rules.txt"
        if not worldview_file.exists():
            raise FileNotFoundError(f"世界観ルールファイルが見つかりません: {worldview_file}")

        with open(worldview_file, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.debug(f"世界観ルール読み込み: {worldview_file}")
        return content

    def load_character_base_prompt(self, character: str) -> str:
        """
        キャラクター個別プロンプト読み込み

        Args:
            character: キャラクター名 (botan, kasho, yuri)

        Returns:
            キャラクター別プロンプトのテキスト

        Raises:
            ValueError: サポートされていないキャラクター名の場合
            FileNotFoundError: プロンプトファイルが見つからない場合
        """
        if character not in self.SUPPORTED_CHARACTERS:
            raise ValueError(
                f"サポートされていないキャラクター: {character}. "
                f"利用可能: {', '.join(self.SUPPORTED_CHARACTERS)}"
            )

        prompt_file = self.prompts_dir / f"{character}_base_prompt.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"キャラクタープロンプトが見つかりません: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.debug(f"キャラクタープロンプト読み込み: {character} ({len(content)} 文字)")
        return content

    def get_combined_prompt(self, character: str) -> str:
        """
        世界観ルール + キャラクタープロンプトを結合

        このメソッドは結果をキャッシュするため、2回目以降は高速です。

        Args:
            character: キャラクター名 (botan, kasho, yuri)

        Returns:
            結合されたプロンプト

        Raises:
            ValueError: サポートされていないキャラクター名の場合
            FileNotFoundError: プロンプトファイルが見つからない場合
        """
        # キャッシュがあれば返す
        if character in self.character_prompts:
            logger.debug(f"キャッシュからプロンプト取得: {character}")
            return self.character_prompts[character]

        # キャラクター別プロンプト読み込み
        character_prompt = self.load_character_base_prompt(character)

        # 結合（世界観ルール + キャラクタープロンプト）
        combined = f"""{self.worldview_rules}

---

{character_prompt}"""

        # キャッシュに保存
        self.character_prompts[character] = combined

        logger.info(
            f"プロンプト結合完了: {character} "
            f"(世界観: {len(self.worldview_rules)} + キャラ: {len(character_prompt)} "
            f"= 合計: {len(combined)} 文字)"
        )

        return combined

    def reload_prompts(self) -> None:
        """
        プロンプトを再読み込み

        開発中にプロンプトファイルを更新した場合、このメソッドを呼び出すことで
        キャッシュをクリアして再読み込みできます。
        """
        logger.info("プロンプトキャッシュをクリアして再読み込み")
        self.worldview_rules = self._load_worldview_rules()
        self.character_prompts.clear()

    def get_all_character_prompts(self) -> Dict[str, str]:
        """
        全キャラクターのプロンプトを取得

        Returns:
            {character: combined_prompt} の辞書
        """
        prompts = {}
        for character in self.SUPPORTED_CHARACTERS:
            prompts[character] = self.get_combined_prompt(character)
        return prompts


# シングルトンインスタンス（オプション）
_prompt_manager_instance: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    シングルトンのPromptManagerインスタンスを取得

    複数箇所から呼び出しても同じインスタンスが返されるため、
    メモリ効率が良くなります。

    Returns:
        PromptManager インスタンス
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance
