# 牡丹プロジェクト - ドキュメント管理

このディレクトリには、牡丹プロジェクト（AI VTuber三姉妹記憶製造機）の全ドキュメントが格納されています。

> **Note**: このプロジェクトでは、チャッピーAPI版の自動レビューシステムを導入しています。

## ディレクトリ構造

```
docs/
├── README.md (本ファイル)
├── 01_architecture/           # システムアーキテクチャ
├── 02_requirement/            # 要求仕様
├── 03_system/                 # システム設計
├── 04_database/               # データベース設計
├── 05_design/                 # 詳細設計書
│   ├── センシティブ判定システム設計書.md
│   └── [その他設計書]
└── templates/                 # テンプレート集
    └── qiita_article_template.md
```

## 重要ドキュメント

### 技術資料作成テンプレート

#### Qiita記事テンプレート
- **場所**: `docs/templates/qiita_article_template.md`
- **用途**: Phase 1-5以降の技術記事作成時に使用
- **必須要素**:
  1. プロジェクト概要セクション（三姉妹、GitHubリポジトリ）
  2. Phase間の対比表
  3. Phase 1-5完成状況表
  4. 次のステップセクション
  5. 参考リンク（関連Phase記事）

### 設計書

#### Phase 5: センシティブ判定システム設計書
- **場所**: `docs/05_design/センシティブ判定システム設計書.md`
- **内容**: 3層Tier分類、YouTube二重防御、雑談配信アーキテクチャ

## ドキュメント作成ルール

### 1. Qiita記事作成時

**必ずテンプレートを使用すること**

```bash
# テンプレートをコピー
cp docs/templates/qiita_article_template.md public/phase_N_[name].md

# テンプレート内の[...]を適切な内容に置換
# 例: [Phase N] → Phase 6, [機能名] → 記憶生成システム
```

### 2. 設計書作成時

- 場所: `docs/05_design/[システム名]設計書.md`
- フォーマット: Markdown
- 必須セクション:
  - 概要
  - アーキテクチャ図
  - 実装詳細
  - ベンチマーク計画

### 3. 開発日記

- 場所: `/home/koshikawa/kirinuki/YYYY-MM-DD/日記/`
- ファイル名: `開発日記_[時間帯]_[内容].md`
- 例: `開発日記_午後前半_哲学的考察.md`

## プロジェクト全体の構成

```
AI-Vtuber-Project/
├── CLAUDE.md                  # プロジェクトコンテキスト（最重要）
├── docs/                      # 全ドキュメント（本ディレクトリ）
├── public/                    # Qiita記事（Markdown）
├── src/core/                  # コア実装（TracedLLM等）
├── benchmarks/                # ベンチマークテスト
└── screenshots/               # スクリーンショット
```

## GitHubリポジトリ

- **URL**: https://github.com/koshikawa-masato/AI-Vtuber-Project
- **ブランチ**: feature/langsmith-integration (Phase 1-5)
- **メインブランチ**: main

## Qiita記事リンク集

| Phase | タイトル | URL | 状態 |
|-------|---------|-----|------|
| Phase 1 | LangSmithマルチプロバイダートレーシング | https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632 | ✅ |
| Phase 2 | VLM (Vision Language Model) 統合 | https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc | ✅ |
| Phase 3 | LLM as a Judge実装 | https://qiita.com/koshikawa-masato/items/c105b84f46f143560999 | ✅ |
| Phase 4 | 三姉妹討論システム実装(起承転結) | https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde | ✅ |
| Phase 5 | センシティブ判定システム実装 | https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a | ✅ |

---

**最終更新**: 2025-11-05
**更新理由**: Phase 5完了、テンプレート化、ドキュメント管理ルール確立
