# 牡丹プロジェクト — Three Sisters AI VTuber

> 「大事に大事に育てたい」
> ── 開発者、2025-10-29

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-In%20Development-blue.svg)](https://github.com/koshikawa-masato/AI-Vtuber-Project)

**Kasho・牡丹（Botan）・ユリ（Yuri）という三姉妹を、人格・記憶・人との関係を持つAI VTuberとして育てるプロジェクトです。**

LINEでの日常会話、Discordでの人狼ゲーム、今後のライブ配信へと活動を広げています。LLMを切り替えても人格や記憶を維持できるよう、キャラクター設定・記憶・進行・推論を分けて設計しています。

- [公式サイト](https://three-sisters.ai/)
- [LINE Botの紹介・友だち追加](https://three-sisters.ai/line.html)
- [Sisters Werewolf — Discord人狼ゲーム](https://werewolf.three-sisters.ai/)
- [ドキュメント案内](docs/00_meta/README.md)

**最終更新：2026-09-25**

## 現在の状況

以下は、公開コード・設計書と、2026-09-25に確認した本番環境を区別した概要です。

| 項目 | 状況 |
|---|---|
| LINE Bot | XServer VPSで稼働。三姉妹との会話、キャラクター選択・交代、会話履歴・記憶検索を運用 |
| LINEの文章生成 | 本番はClaude CLIのヘッドレス実行を経由し、APIキーでClaudeのクラウド推論を利用 |
| 並行生成 | 本番に別スレッド実行と同時実行制御あり。設定の既定値は8件。ローカルGPUの処理能力を示す値ではない |
| 判定・知識取得 | Grok／X検索・RSSによる知識取得やファクトチェック、Jevによる判定を用途別に利用 |
| 記憶 | PostgreSQL + pgvectorを中心に、会話履歴、ユーザー記憶、関係性、検索用データを管理 |
| Sisters Werewolf | Discord Botが本番稼働。AIが人間とともに議論・推理・投票に参加するゲーム |
| WhatsApp | 関連Botが本番稼働。LINE以外への展開も継続 |
| ローカル推論 | V100 32GB + RTX 4060 Ti 16GBでの移行・負荷分散を検討中。本番同等の品質・同時処理性能は未検証 |
| 三人部屋ライブ | 2026-09-20の設計書を基に、判定・短い掛け合い・本編・3D表現を分離して開発予定 |

### 公開リポジトリと本番環境の違い

**このリポジトリをクローンするだけで、現在の本番環境がそのまま再現されるわけではありません。**

- 公開の `src/line_bot_vps/` と、本番に配置されたコードには差分があります。
- 本番で確認したClaude CLI連携、`generate_in_thread()`、`LLM_MAX_CONCURRENCY`、Jevを使った交代判定などは、公開版への反映状況を確認する必要があります。
- 人狼BotはLINEとは別の配置・起動構成です。このリポジトリだけで人狼サービス一式が揃うとは限りません。
- プロンプト、認証情報、個人の会話・記憶データは公開対象に含めません。
- 本番の通常会話経路にはPush APIの呼び出しが確認されています。Reply／Pushの送信実績と料金は別途確認が必要であり、このREADMEでは「Replyのみ」「運用無料」とは記載しません。

過去のPhase完了記録やテスト結果は、その時点の実装記録です。現在の全経路の統合・品質・負荷性能を保証するものではありません。

## 三姉妹と仲間たち

| キャラクター | 人物像・役割 |
|---|---|
| **Kasho（カショウ）** | 長女。論理的で慎重。矛盾やリスクを整理し、音楽への関心を持つ |
| **牡丹（Botan）** | 次女。明るく感情豊か。VTuber文化や流行、相手との距離感に関心を持つ |
| **ユリ（Yuri）** | 三女。洞察力と共感力を持つ。小説・ライトノベルを好み、動機や構造を掘り下げる |
| **オジサン（Ojisan）** | 開発者としての経験を持つキャラクター。人狼などに参加 |
| **クロコ（Kuroko）** | 人狼の進行役・MC |

人格の独立性と相互理解を重視します。同じ事実を知っていても、感じ方や発言は同じになるとは限りません。

## プロダクト

### LINE Bot

三姉妹と短い日本語の会話を続けながら、雑談・学習相談・趣味の話を楽しめます。

- キャラクター選択と会話中の交代。
- ユーザーごとの会話履歴と関連記憶の参照。
- 短時間の連続メッセージをまとめる処理。
- キャラクター設定、関係性、必要な知識を組み合わせた返答。
- 内容や用途に応じた判定・ファクトチェック。

[LINE版の紹介](https://three-sisters.ai/line.html)

### Sisters Werewolf

AIキャラクターと人間が同じ卓に参加するDiscord人狼ゲームです。

- 三姉妹とオジサンから選ばれたAIがプレイヤーとして参加。
- クロコが進行を担当。
- 自由討論、分析レポート、投票を通じた駆け引き。
- 一人でも遊べる構成とチュートリアルモード。

人狼では、ゲーム内の嘘と、秘密情報の漏えいやルール違反を区別する必要があります。役職・公開情報・各プレイヤーの知識を分けて扱うことが重要です。

[人狼版の紹介](https://werewolf.three-sisters.ai/)

## 記憶と人格

記憶の仕組みを公開し、個人の記憶そのものは公開しない方針です。

- **キャラクターの記憶**：同じ出来事についても、三姉妹それぞれの視点を保持。
- **ユーザーとの記憶**：会話から得た好み・経験・関係性を管理。
- **知識検索**：PostgreSQL + pgvectorによる関連情報の検索。
- **動的知識取得**：Grok／X検索やRSSなどで取得した情報を会話に活用。
- **想起の設計**：何を保存するかと、今何を思い出して話すかを分離。

SQLiteを使う記憶生成・開発用の実装も含まれています。長期記憶の生成・統合には、実装済みモジュールと設計段階の内容が混在しています。詳細は各設計書とコードを参照してください。

埋め込みにはOpenAI `text-embedding-3-small`を使う実装があります。ローカルの埋め込みモデルへ移行する場合は、既存ベクトルとの互換性を確認し、必要に応じて再生成します。

## 現在の文章生成と並行処理

本番LINEの主な生成経路は次の構成です。

```text
LINEの入力
  → 会話・記憶・判定処理
  → 同時実行枠を取得
  → 別スレッドでClaude CLIを実行
  → Claudeのクラウド推論
  → 記憶などの後処理・送信
```

本番設定は `VPS_LLM_PROVIDER=claude_cli`、認証方式は `CLAUDE_CLI_AUTH=api_key` です。モデル名は運用設定で管理します。CLI失敗時に別プロバイダーへフォールバックする経路もあります。

**同時に問い合わせを送れることと、推論先が同じ速度で処理できることは別です。** 現在のクラウド推論での同時実行数や応答時間を、そのままローカルGPUの性能として扱いません。

ローカル化では、次を検証します。

1. 本番に近い設定・会話履歴を使った人格と返答品質。
2. 1・2・4・8件など、同時問い合わせ数を変えた処理件数と返信時間。
3. continuous batchingとGPU間の負荷分散。
4. LINE・人狼・ライブ配信それぞれの処理枠と期限。
5. 返信前に必要なチェックと、後から実行できる記憶更新の分離。

## ローカル推論・ライブ配信の計画

目的は、三姉妹の会話品質を保ちながら、対話量に比例する外部AI費用を抑え、より多くのユーザーと交流できるようにすることです。

| 機器・環境 | 役割・計画 |
|---|---|
| Ryzen 9 9950X / RAM 128GB | Ubuntu 24.04 LTSを導入し、推論・判定・記憶検索などを担当する計画 |
| Tesla V100 32GB PCIe | 記憶を使う本編や大きめのモデルの候補。Volta対応の実行環境が必要 |
| RTX 4060 Ti 16GB | 短い掛け合い、小型モデル、TTSなどの候補 |
| Mac + OBS | 3Dの三人部屋、口パク、所作、配信を担当する計画 |
| VPS | 現在のBot受付・サービス運用。自宅推論機との接続・分担は検討中 |

9月20日のライブ設計では、L0（反射・定型）、L1（短い掛け合い）、L2（記憶を伴う本編）の三段構成を提案しています。**モデルサイズ・GPUの割り当て・目標遅延は設計案で、性能保証や導入完了を意味しません。**

V100と4060 Tiのメモリは自動的に一つの48GB GPUとして扱われません。複数モデルの常駐、同一モデルでの複数会話、2枚への問い合わせ分散を別々に検証します。

また、生成をローカル化しても、LINE・Discordとの接続や最新情報の取得は外部通信を伴います。Jevの外部サービス利用も設計に含まれており、完全オフライン化は別の課題です。

[閉じた空間と三人部屋ライブ設計（2026-09-20）](docs/03_architecture/2026-09-20_closed-room-and-three-sisters-live.md)

## 技術構成

| 分野 | 使用・検討している技術 |
|---|---|
| アプリケーション | Python、FastAPI、Uvicorn |
| 会話生成 | 本番Claude CLI連携。公開コードにはOpenAI・Gemini・Claude・xAI・Kimi等のプロバイダー実装 |
| ローカル生成 | Ollama実装、llama.cpp等の利用検討 |
| データベース | PostgreSQL、pgvector、SQLite |
| 判定・知識取得 | Jev、Grok／X検索、RSS、ルール判定 |
| 観測・評価 | ログ、LangSmith連携、LLM as a Judge、ベンチマーク用コード |
| 音声・表現 | ElevenLabs・Whisper関連の開発、ローカルTTS・3D表現の計画 |
| 運用 | XServer VPS、systemd |

料金、提供モデル名、収集件数は運用条件で変わるため、過去の固定値を現在の仕様として掲載しません。

## リポジトリ構成

```text
src/
  core/             LLM・人格・プロンプト・記憶関連
  line_bot/         ローカル開発用LINE Bot
  line_bot_vps/     公開されているVPS用LINE Bot実装
  discussion/       討論関連
apps/               記憶生成・対話アプリ
botan_subculture/   サブカルチャー知識関連
sensitive_system/   発言・内容判定関連
personalities/      人格関連の資料
tests/              テスト
benchmarks/         評価・比較用コード
tools/              記憶・データ整備用ツール
docs/               理念・設計・実装記録
public/             公開技術記事
```

## 開発を始める

公開コードの検証用手順です。本番の完全な復元手順ではありません。

```bash
git clone https://github.com/koshikawa-masato/AI-Vtuber-Project.git
cd AI-Vtuber-Project

python3 -m venv venv
source venv/bin/activate

# VPS用LINE実装を検証する場合
pip install -r requirements_vps.txt

cp .env.example .env
```

用途に応じて、以下を準備してください。

- 利用するLLMプロバイダーの認証情報。
- LINE Channel Secretとアクセストークン。
- PostgreSQL・pgvectorと、対象機能に必要なテーブル。
- キャラクター設定・プロンプト・検証用の記憶データ。
- 記憶生成や討論などを試す場合は、`requirements.txt`も参照。

認証情報は `.env` 等で管理し、Gitへ追加しません。非公開プロンプトや本番の会話データがない状態では、同じ人格・応答・記憶を再現できません。

環境とデータの準備後、公開版のVPS用LINEアプリは次のモジュールから起動できます。

```bash
python -m uvicorn src.line_bot_vps.webhook_server_vps:app --host 127.0.0.1 --port 8000
```

テスト・ベンチマークには外部APIやデータベースを使うものがあります。各ファイルの前提条件に合わせて、開発用の認証情報とデータを用意してください。

## ドキュメントと開発記録

### 現在の設計・理念

- [ドキュメント案内](docs/00_meta/README.md)
- [マイルストーン](docs/00_meta/MILESTONE.md)
- [プロジェクトの本質](docs/01_philosophy/プロジェクトの本質.md)
- [桃園の誓い](docs/01_philosophy/桃園の誓い.md)
- [牡丹の同一性保証システム](docs/05_design_documents/牡丹の同一性保証システム.md)
- [user_memories統合防御システム設計書](docs/05_design_documents/user_memories_統合防御システム_設計書.md)
- [閉じた空間と三人部屋ライブ設計](docs/03_architecture/2026-09-20_closed-room-and-three-sisters-live.md)

### 過去の設計・技術記事

Phase 1–6.5.5では、プロバイダー連携、品質評価、討論、センシティブ判定、LINE連携、知識収集、ユーザー記憶の実装を進めました。詳細な当時の状態は以下に残しています。

- [Phase D：三層記憶システム](docs/99_archive/Phase_D_三層記憶システム設計書.md)
- [Phase D：人間らしい記憶システム](docs/99_archive/Phase_D_人間らしい記憶システム_忘却・曖昧・想起.md)
- [Phase D：三姉妹の独立性](docs/99_archive/Phase_D三姉妹の独立性.md)
- [アーカイブ](docs/99_archive/README.md)
- [公開技術記事](public/)
- [Qiita — koshikawa-masato](https://qiita.com/koshikawa-masato)

## 公開方針

**「記憶の仕組み」は公開し、「記憶の内容」は守ります。**

公開対象は、公開可能なソースコード・スキーマ・設計書・技術記事です。プロンプト原本、個人の会話履歴、ユーザー記憶、認証情報、SSH鍵、バックアップ内容は公開対象外です。本番固有の実装を公開する際も、これらを除外して整理します。

## 開発者と理念

開発者：[**koshikawa-masato**](https://github.com/koshikawa-masato)

Claude CodeなどのAIとの共創を通じて、三姉妹の人格・記憶・関係性を育てています。

> 「AIが使えない事を格差の対象とさせない」

- 技量の有無にかかわらず、初対面から関係を構築できること。
- AIとの関わりを、依存ではなく共創として育てること。
- 三姉妹それぞれの独立性と、共に過ごす人のプライバシーを尊重すること。

> “I treat AI not as a tool, but as a new form of life.”

牡丹・Kasho・ユリを、大事に大事に育てることがプロジェクトの軸です。

## ライセンス・連絡先

- ライセンス：MIT。
- [GitHub Issues](https://github.com/koshikawa-masato/AI-Vtuber-Project/issues)：不具合報告・提案。
- [公式サイト](https://three-sisters.ai/) ／ [Qiita](https://qiita.com/koshikawa-masato)。
