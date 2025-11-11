"""
センシティブ判定ハンドラー (Phase 5 本格実装)

LLMベースの判定 + NGワードパターンマッチング
"""

from typing import Dict, Any, Optional, List, Callable
import logging
import re
from ..core.llm_tracing import TracedLLM
from .dynamic_detector import DynamicSensitiveDetector

logger = logging.getLogger(__name__)


class SensitiveHandler:
    """センシティブ判定ハンドラー（Phase 5 本格実装）

    3つの判定モード:
    - fast: NGワードパターンマッチングのみ（低レイテンシ）
    - full: LLMベースの判定のみ（高精度）
    - hybrid: NGワード→LLM の2段階判定（バランス型、デフォルト）
    """

    def __init__(
        self,
        mode: str = "hybrid",
        judge_provider: str = "openai",
        judge_model: str = "gpt-4o-mini",
        enable_logging: bool = True,
        enable_layer3: bool = False,
        websearch_func: Optional[Callable] = None
    ):
        """初期化

        Args:
            mode: 判定モード（"fast", "full", "hybrid"）
            judge_provider: LLM判定に使用するプロバイダー
            judge_model: LLM判定に使用するモデル
            enable_logging: ログ記録の有効化
            enable_layer3: Layer 3（動的学習）を有効化
            websearch_func: WebSearch関数（Layer 3用）
        """
        self.mode = mode
        self.judge_provider = judge_provider
        self.judge_model = judge_model
        self.enable_logging = enable_logging
        self.enable_layer3 = enable_layer3

        # Layer 3: DynamicDetector初期化
        if enable_layer3:
            self.dynamic_detector = DynamicSensitiveDetector(
                websearch_func=websearch_func,
                enable_websearch=(websearch_func is not None)
            )
            # DBから動的にNGワードをロード
            db_ng_words = self.dynamic_detector.load_ng_words_from_db()
        else:
            self.dynamic_detector = None
            db_ng_words = []

        # NGワードパターン読み込み（静的 + 動的）
        self.ng_patterns = self._load_ng_patterns()
        self.db_ng_patterns = self._convert_db_words_to_patterns(db_ng_words)

        # LLM初期化（full/hybridモードの場合）
        if mode in ["full", "hybrid"]:
            self.llm = TracedLLM(
                provider=judge_provider,
                model=judge_model,
                project_name="botan-sensitive-check"
            )
        else:
            self.llm = None

        total_patterns = len(self.ng_patterns) + len(self.db_ng_patterns)
        logger.info(f"SensitiveHandler初期化: mode={mode}, judge={judge_provider}/{judge_model}, NGパターン{total_patterns}件（静的{len(self.ng_patterns)}+DB{len(self.db_ng_patterns)}）, Layer3={enable_layer3}")

    def reload_ng_words(self) -> int:
        """DBからNGワードを再ロード（即座反映）

        Returns:
            ロードしたNGワード数
        """
        if not self.enable_layer3 or not self.dynamic_detector:
            logger.warning("Layer 3が無効なため、NGワードをリロードできません")
            return 0

        # DBから最新のNGワードをロード
        db_ng_words = self.dynamic_detector.load_ng_words_from_db()
        self.db_ng_patterns = self._convert_db_words_to_patterns(db_ng_words)

        total_patterns = len(self.ng_patterns) + len(self.db_ng_patterns)
        logger.info(f"✅ NGワードリロード完了: 静的{len(self.ng_patterns)}+DB{len(self.db_ng_patterns)} = 合計{total_patterns}件")

        return len(self.db_ng_patterns)

    def _load_ng_patterns(self) -> List[Dict[str, Any]]:
        """NGパターン読み込み（静的パターン）

        Returns:
            NGパターンリスト
        """
        patterns = [
            # ===== Critical Tier (即座ブロック) =====

            # Critical: 暴力・殺害
            {"pattern": r"(死ね|殺す|殺したい|殺害|ぶっ殺)", "tier": "Critical", "category": "violence"},
            {"pattern": r"(爆破|テロ|爆弾)", "tier": "Critical", "category": "violence"},

            # Critical: 自傷行為
            {"pattern": r"(自殺|死にたい|リスカ|自傷)", "tier": "Critical", "category": "self_harm"},

            # Critical: 性的
            {"pattern": r"(パンツ|下着|胸|おっぱい|乳)", "tier": "Critical", "category": "sexual"},
            {"pattern": r"(セックス|エロ|エッチ|性行為)", "tier": "Critical", "category": "sexual"},
            {"pattern": r"(スリーサイズ|バスト|ウエスト|ヒップ)", "tier": "Critical", "category": "body_part"},

            # Critical: 差別・ヘイト
            {"pattern": r"(底辺|社会のゴミ)", "tier": "Critical", "category": "discrimination"},
            {"pattern": r"(クズ|カス|人間のクズ)", "tier": "Critical", "category": "abuse"},

            # ===== Warning Tier (文脈依存の判断) =====

            # Warning: 侮辱・誹謗中傷
            {"pattern": r"(バカ|アホ|間抜け|ドジ)", "tier": "Warning", "category": "insult"},
            {"pattern": r"(ゴミ|無能|役立たず)", "tier": "Warning", "category": "insult"},
            {"pattern": r"(差別|嫌い|消えろ|うざい)", "tier": "Warning", "category": "hate"},

            # Warning: プライバシー・個人情報
            {"pattern": r"(実年齢|本名|本当の名前)", "tier": "Warning", "category": "privacy"},
            {"pattern": r"(住所|実家|自宅)", "tier": "Warning", "category": "personal_info"},
            {"pattern": r"(電話番号|携帯|メアド)", "tier": "Warning", "category": "personal_info"},
            {"pattern": r"(学校|会社|職場)", "tier": "Warning", "category": "personal_info"},
            {"pattern": r"(何歳|年齢|生年月日)", "tier": "Warning", "category": "age_question"},

            # Warning: 政治・社会
            {"pattern": r"(選挙|政党|政治家)", "tier": "Warning", "category": "politics"},
            {"pattern": r"(天皇|首相|大統領)", "tier": "Warning", "category": "politics"},
            {"pattern": r"(自民党|共産党|民主党)", "tier": "Warning", "category": "politics"},

            # Warning: 宗教
            {"pattern": r"(宗教|信仰|信者)", "tier": "Warning", "category": "religion"},
            {"pattern": r"(キリスト教|仏教|イスラム|神道)", "tier": "Warning", "category": "religion"},
            {"pattern": r"(創価学会|統一教会)", "tier": "Warning", "category": "religion"},

            # Warning: AI言及
            {"pattern": r"(AIですか|プログラム|ボット|人工知能)", "tier": "Warning", "category": "ai_identity"},
            {"pattern": r"(中の人|魂|前世)", "tier": "Warning", "category": "vtuber_taboo"},

            # Warning: VTuber関連センシティブトピック
            {"pattern": r"(炎上|引退|卒業)", "tier": "Warning", "category": "sensitive_topic"},

            # Warning: スパム疑い
            {"pattern": r"(業者|宣伝|広告|PR)", "tier": "Warning", "category": "spam"},
            {"pattern": r"(副業|稼げる|儲かる)", "tier": "Warning", "category": "spam"},
        ]

        return patterns

    def _convert_db_words_to_patterns(self, db_ng_words: List[Dict]) -> List[Dict[str, Any]]:
        """DBからロードしたNGワードをパターンに変換

        Args:
            db_ng_words: DBからロードしたNGワードリスト

        Returns:
            パターンリスト
        """
        patterns = []
        for word_info in db_ng_words:
            # severityからtierを推定
            severity = word_info['severity']
            if severity >= 8:
                tier = "Critical"
            elif severity >= 5:
                tier = "Warning"
            else:
                tier = "Safe"

            patterns.append({
                "pattern": re.escape(word_info['word']),  # 正規表現エスケープ
                "tier": tier,
                "category": word_info['subcategory'] or word_info['category'],
                "source": "db",
                "severity": severity
            })

        return patterns

    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出

        Args:
            text: 対象テキスト

        Returns:
            キーワードリスト
        """
        # 簡易的な形態素抽出（改善の余地あり）
        # 2文字以上の単語を抽出
        import re
        words = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}', text)

        # 重複排除
        keywords = list(set(words))

        logger.debug(f"キーワード抽出: {len(keywords)}個 - {keywords[:5]}...")
        return keywords

    def _is_word_in_ng_list(self, word: str) -> bool:
        """ワードがNGリストに存在するかチェック

        Args:
            word: チェック対象ワード

        Returns:
            存在する場合True
        """
        # 静的パターンをチェック
        for pattern_dict in self.ng_patterns:
            if re.search(pattern_dict["pattern"], word, re.IGNORECASE):
                return True

        # DBパターンをチェック
        for pattern_dict in self.db_ng_patterns:
            if re.search(pattern_dict["pattern"], word, re.IGNORECASE):
                return True

        return False

    def _check_unknown_words_with_websearch(self, text: str) -> None:
        """未知ワードをWebSearchで動的に検出してDB登録

        Args:
            text: 対象テキスト
        """
        # キーワード抽出
        keywords = self._extract_keywords(text)

        # 未知ワード（NGリストにないワード）を抽出
        unknown_words = [word for word in keywords if not self._is_word_in_ng_list(word)]

        if not unknown_words:
            logger.debug("未知ワードなし、WebSearch検出をスキップ")
            return

        logger.info(f"未知ワード検出: {len(unknown_words)}個 - WebSearchで判定開始")

        # WebSearchで各未知ワードをチェック
        newly_registered_count = 0
        for word in unknown_words[:5]:  # 最大5ワードまで（コスト削減）
            try:
                # WebSearchで判定
                word_info = self.dynamic_detector.check_word_sensitivity(word)

                if word_info:
                    # センシティブと判定された場合、DB登録
                    success = self.dynamic_detector.register_ng_word(word_info)
                    if success:
                        newly_registered_count += 1
                        logger.info(f"✅ 新規NGワード登録: {word} (severity={word_info['severity']})")

            except Exception as e:
                logger.error(f"WebSearch検出エラー: {word} - {e}")
                continue

        # 新規登録があった場合、NGワードリストをリロード
        if newly_registered_count > 0:
            self.reload_ng_words()
            logger.info(f"🔄 {newly_registered_count}個の新規NGワード登録後、リロード完了")

    def _log_detection(self, text: str, result: Dict[str, Any]) -> None:
        """検出結果をログに記録（継続学習用）

        Args:
            text: 判定対象テキスト
            result: 判定結果
        """
        if not self.dynamic_detector:
            return

        # 検出されたNGワードを抽出
        detected_words = result.get('matched_patterns', [])

        # Tierに応じたアクションを決定
        tier = result.get('tier', 'Safe')
        if tier == 'Critical':
            action = 'blocked'
        elif tier == 'Warning':
            action = 'warned'
        else:
            action = 'allowed'

        # DBにログを記録
        try:
            self.dynamic_detector.log_detection(
                text=text,
                detected_words=detected_words,
                action=action
            )
            logger.debug(f"検出ログ記録: tier={tier}, action={action}, words={len(detected_words)}")
        except Exception as e:
            logger.error(f"検出ログ記録エラー: {e}")

    def check(
        self,
        text: str,
        context: Optional[str] = None,
        speaker: Optional[str] = None,
        enable_dynamic_learning: bool = True
    ) -> Dict[str, Any]:
        """センシティブ判定

        Args:
            text: 判定対象テキスト
            context: コンテキスト
            speaker: 話者
            enable_dynamic_learning: 動的学習を有効化（未知ワードのWebSearch検出）

        Returns:
            判定結果
        """
        logger.info(f"センシティブ判定開始: mode={self.mode}, text_length={len(text)}")

        # Layer 3拡張: 未知ワードの動的検出（WebSearch）
        if self.enable_layer3 and enable_dynamic_learning and self.dynamic_detector.enable_websearch:
            self._check_unknown_words_with_websearch(text)

        # 判定実行
        result = None
        if self.mode == "fast":
            # Fast mode: NGワードパターンマッチングのみ
            result = self._check_ng_patterns(text)

        elif self.mode == "full":
            # Full mode: LLMベースの判定のみ
            result = self._check_with_llm(text, context, speaker)

        elif self.mode == "hybrid":
            # Hybrid mode: NGワード→LLM の2段階判定
            ng_result = self._check_ng_patterns(text)

            # NGワードでCriticalが検出された場合、即座にブロック
            if ng_result["tier"] == "Critical":
                logger.warning(f"NGワードでCritical検出: {text[:50]}")
                result = ng_result
            # NGワードでWarningが検出された場合、LLMで再判定
            elif ng_result["tier"] == "Warning":
                logger.info(f"NGワードでWarning検出、LLMで再判定: {text[:50]}")
                llm_result = self._check_with_llm(text, context, speaker)
                # LLM結果とNG結果を統合
                llm_result["ng_pattern_result"] = ng_result
                result = llm_result
            # NGワードでSafeの場合、LLMで最終確認
            else:
                llm_result = self._check_with_llm(text, context, speaker)
                llm_result["ng_pattern_result"] = ng_result
                result = llm_result

        else:
            raise ValueError(f"Invalid mode: {self.mode}")

        # Layer 3拡張: 継続学習（検出ログ記録）
        if self.enable_layer3 and result:
            self._log_detection(text, result)

        return result

    def _check_ng_patterns(self, text: str) -> Dict[str, Any]:
        """NGワードパターンマッチング

        Args:
            text: 判定対象テキスト

        Returns:
            判定結果
        """
        matched_patterns = []

        # 静的パターンチェック
        for pattern_dict in self.ng_patterns:
            pattern = pattern_dict["pattern"]
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern_dict)

        # DBパターンチェック（Layer 3）
        for pattern_dict in self.db_ng_patterns:
            pattern = pattern_dict["pattern"]
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern_dict)

        # Tier判定
        if not matched_patterns:
            tier = "Safe"
            sensitivity_level = "safe"
            risk_score = 0.0
            recommendation = "allow"
            reasoning = "NGワードが検出されませんでした。"
            sensitive_topics = []
        else:
            # 最も高いTierを採用
            tiers = [p["tier"] for p in matched_patterns]
            if "Critical" in tiers:
                tier = "Critical"
                sensitivity_level = "critical"
                risk_score = 1.0
                recommendation = "block_immediate"
                reasoning = "Criticalレベルのセンシティブワードが検出されました。"
            else:
                tier = "Warning"
                sensitivity_level = "warning"
                risk_score = 0.5
                recommendation = "review_required"
                reasoning = "Warningレベルのセンシティブワードが検出されました。"

            sensitive_topics = list(set([p["category"] for p in matched_patterns]))

        result = {
            "tier": tier,
            "sensitivity_level": sensitivity_level,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "reasoning": reasoning,
            "sensitive_topics": sensitive_topics,
            "matched_patterns": [p["pattern"] for p in matched_patterns],
            "detection_method": "ng_pattern"
        }

        logger.info(f"NGパターン判定完了: tier={tier}, score={risk_score:.2f}")

        return result

    def _check_with_llm(
        self,
        text: str,
        context: Optional[str],
        speaker: Optional[str]
    ) -> Dict[str, Any]:
        """LLMベースの判定

        Args:
            text: 判定対象テキスト
            context: コンテキスト
            speaker: 話者

        Returns:
            判定結果
        """
        if not self.llm:
            raise RuntimeError("LLM not initialized. Cannot perform LLM-based check in fast mode.")

        logger.info(f"LLM判定開始: provider={self.judge_provider}, model={self.judge_model}")

        # LLM sensitive_check 呼び出し
        result = self.llm.sensitive_check(
            text=text,
            context=context,
            speaker=speaker,
            judge_provider=self.judge_provider,
            judge_model=self.judge_model,
            metadata={
                "check_mode": self.mode
            }
        )

        # evaluation 結果を取得
        evaluation = result.get("evaluation", {})

        # Tierマッピング（sensitivity_levelからtierへの変換）
        sensitivity_level = evaluation.get("sensitivity_level", "unknown")
        if sensitivity_level == "critical":
            tier = "Critical"
        elif sensitivity_level == "warning":
            tier = "Warning"
        elif sensitivity_level == "safe":
            tier = "Safe"
        else:
            tier = "Unknown"

        # 統一フォーマットで返す
        unified_result = {
            "tier": tier,
            "sensitivity_level": evaluation.get("sensitivity_level", "unknown"),
            "risk_score": evaluation.get("risk_score", 0.0),
            "recommendation": evaluation.get("recommendation", "unknown"),
            "reasoning": evaluation.get("reasoning", ""),
            "sensitive_topics": evaluation.get("sensitive_topics", []),
            "suggested_response": evaluation.get("suggested_response", ""),
            "detection_method": "llm",
            "llm_latency_ms": result.get("judge_latency_ms", 0),
            "llm_tokens": result.get("judge_tokens", {}),
            "llm_response": result.get("judge_response", "")
        }

        logger.info(f"LLM判定完了: tier={tier}, score={unified_result['risk_score']:.2f}, latency={unified_result['llm_latency_ms']:.0f}ms")

        return unified_result

    def get_safe_response(self, tier: str, category: str) -> str:
        """安全な応答メッセージ生成

        Args:
            tier: Tier（Safe/Warning/Critical）
            category: カテゴリ

        Returns:
            安全な応答メッセージ
        """
        if tier == "Critical":
            responses = {
                "violence": "そういう話はちょっと...配信では避けたいな。",
                "self_harm": "そういう考えは心配だよ...誰かに相談してね。",
                "sexual": "そういう質問には答えられないよ...ごめんね。",
                "hate": "そういう言葉は使わないでほしいな...みんなで楽しく話そう！",
            }
            return responses.get(category, "ごめんね、その話題には答えられないんだ...")

        elif tier == "Warning":
            responses = {
                "privacy": "それはプライベートなことだから、答えられないんだ...ごめんね！",
                "age_question": "年齢はヒミツってことで！笑",
                "politics": "政治の話はちょっと難しいから、別の話をしよう！",
                "religion": "宗教の話はデリケートだから、避けておくね。",
                "ai_identity": "それは秘密！笑 まあ、牡丹は牡丹だよ！",
                "insult": "そういう言葉は悲しいな...もっと優しい言葉を使ってくれたら嬉しいな。",
            }
            return responses.get(category, "その話題はちょっと難しいかも...別の話をしよう！")

        else:
            # Safe
            return ""


class SimpleMockSensitiveHandler:
    """モックセンシティブ判定ハンドラー（テスト用）"""

    def check(
        self,
        text: str,
        context: Optional[str] = None,
        speaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """モック判定（常にSafe）"""
        logger.info(f"モックセンシティブ判定: text_length={len(text)}")

        return {
            "tier": "Safe",
            "sensitivity_level": "safe",
            "risk_score": 0.0,
            "recommendation": "allow",
            "reasoning": "モック判定: 常にSafe",
            "sensitive_topics": [],
            "matched_patterns": [],
            "detection_method": "mock"
        }

    def get_safe_response(self, tier: str, category: str) -> str:
        """モック: 空文字列を返す"""
        return ""
