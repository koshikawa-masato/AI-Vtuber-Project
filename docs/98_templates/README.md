# テンプレート集

このディレクトリには、プロジェクトで使用する各種テンプレートが格納されています。

## Qiita記事テンプレート

### ファイル名
`qiita_article_template.md`

### 用途
Phase 1-5以降の技術記事を作成する際に使用します。

### 使い方

#### 1. テンプレートをコピー

```bash
# publicディレクトリにコピー
cp docs/templates/qiita_article_template.md public/phase_N_[name].md

# 例: Phase 6 記憶生成システム
cp docs/templates/qiita_article_template.md public/phase6_memory_generation.md
```

#### 2. プレースホルダーを置換

テンプレート内の以下のプレースホルダーを適切な内容に置換してください：

| プレースホルダー | 置換例 |
|----------------|--------|
| `[Phase N]` | Phase 6 |
| `[タイトル]` | 記憶生成システム実装 |
| `[サブタイトル]` | AI VTuberに人生の記憶を |
| `[今回のPhaseで実装した機能の概要]` | 過去の人生を生成し長期記憶として保存する機能 |
| `[適切なタグ1]` | Memory |
| `[適切なタグ2]` | SQLite |
| `[今回追加した機能]` | 記憶生成システム |
| `[技術1]` | SQLite |
| `[技術2]` | LangChain Memory |
| `[機能名]` | 記憶生成システム |
| `[N-1]` | 5 |
| `[前Phaseの名前]` | センシティブ判定システム |

#### 3. 必須セクションの確認

以下のセクションが全て含まれていることを確認してください：

- ✅ はじめに：AI VTuber「牡丹プロジェクト」とは
- ✅ 三姉妹の構成
- ✅ GitHubリポジトリリンク
- ✅ Phase N: [機能名]の重要性
- ✅ 前Phaseとの対比セクション
- ✅ 実装の核心部分
- ✅ ベンチマーク結果
- ✅ LangSmith統合
- ✅ まとめセクション
  - Phase N の成果
  - Phase [N-1] との対比
  - Phase 1-5の完成状況表
  - 次のステップ
- ✅ 参考リンク（Phase 1-5へのリンク）

#### 4. Qiitaへの公開

```bash
# Qiita CLIで公開
npx qiita publish phase6_memory_generation
```

### テンプレートの構造

```
1. FrontMatter (メタデータ)
2. はじめに（プロジェクト概要）
3. Phase N の説明
4. 技術セクション
5. 前Phaseとの対比
6. 実装詳細
7. ベンチマーク
8. LangSmith統合
9. トラブルシューティング
10. まとめ（Phase完成状況表含む）
11. 参考リンク
```

### 注意事項

1. **GitHubリポジトリURL**: 必ず `https://github.com/koshikawa-masato/AI-Vtuber-Project` に更新
2. **Phase完成状況表**: 新しいPhaseを追加する際は、表に新しい行を追加
3. **参考リンク**: 全てのPhase記事へのリンクを含める
4. **三姉妹の性格**: Kasho（論理的）、牡丹（ギャル系）、ユリ（調整役）を正しく記載

### Phase完成状況表の更新方法

新しいPhase Nを追加する場合：

```markdown
| Phase | 内容 | 記事 | 状態 |
|-------|------|------|------|
| Phase 1 | LangSmithマルチプロバイダートレーシング | [記事](https://qiita.com/koshikawa-masato/items/bb95295630c647eb5632) | ✅ |
| Phase 2 | VLM (Vision Language Model) 統合 | [記事](https://qiita.com/koshikawa-masato/items/fd684b963bad149d3ddc) | ✅ |
| Phase 3 | LLM as a Judge実装 | [記事](https://qiita.com/koshikawa-masato/items/c105b84f46f143560999) | ✅ |
| Phase 4 | 三姉妹討論システム実装(起承転結) | [記事](https://qiita.com/koshikawa-masato/items/02bdbaa005949ff8cbde) | ✅ |
| Phase 5 | センシティブ判定システム実装 | [記事](https://qiita.com/koshikawa-masato/items/2bf3e024325176d3400a) | ✅ |
| **Phase N** | **[新機能名]** | **本記事** | ✅ |
```

---

**テンプレート作成日**: 2025-11-05
**最終更新**: 2025-11-05
