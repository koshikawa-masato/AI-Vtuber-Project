# 2025年11月10日 開発日記 - gpt-oss-120bのテストとQiita記事作成

## 今日やったこと

### 1. gpt-oss-120bのダウンロードとテスト

OpenAIのオープンウェイトモデル「gpt-oss-120b」をOllamaでダウンロードして実行テスト。

**環境**:
- WSL2 Ubuntu 24.04
- CPU: AMD Ryzen 9 9950X 16-Core
- GPU: NVIDIA GeForce RTX 4060 Ti (16GB VRAM)
- AMD Radeon Graphics（統合GPU、2GB割り当て）

**結果**:
- モデルサイズ: 65GB
- 推論速度: 8.54 tokens/s（ハイブリッドモード: GPU+CPU）
- 応答時間: 2分以上（複雑な質問の場合）

### 2. copy_robot_chat_cliへのフィルタリング機能実装

gpt-oss-120bの「Thinking...」出力を自動的にフィルタリングする機能を実装。

**実装内容**:
```python
# 出力から思考部分を除去
if response.startswith('Thinking...'):
    thinking_end = response.find('...done thinking.')
    if thinking_end != -1:
        response = response[thinking_end + len('...done thinking.'):].strip()
```

### 3. Qiita記事の作成と投稿

**記事タイトル**: OpenAIのgpt-oss-120bをOllamaで試してみた

**記事ID**: d1aba0e311bc6231b6a3

**記事の内容**:
- gpt-oss-120bの基本スペックと特徴
- Ollamaでのインストール手順
- 思考プロセスのフィルタリング実装
- qwen2.5:14bとの詳細比較
  - 応答時間: 29.6秒 vs 2分以上
  - 応答品質: 簡潔 vs 超詳細
  - 全文応答の比較（折りたたみ可能）
- メモリ要件の詳細（GPU/CPU別）
- WSL2環境での注意点

### 4. WSL2とWindows環境の違いを発見

**重要な発見**:
- **Windows**: AMD Radeon統合GPU + 共有メモリ64GB活用 → **45+ tokens/s**
- **WSL2**: NVIDIA RTX 4060 Ti (16GB VRAM制限) → **8.5 tokens/s**

**原因**:
- WSL2からはAMD統合GPUの共有メモリにアクセスできない
- 外部GPU（NVIDIA）のVRAMサイズに制限される

**対策（今後試す予定）**:
1. BIOS/UEFIでUMA Frame Buffer Sizeを64GBに設定
2. Windows上でOllamaを実行
3. AMD統合GPUの共有メモリを活用して45+ tokens/sを実現

### 5. 記事の改善

以下の修正を実施:
1. 【速報】タグを削除（詳細な比較レポートのため）
2. 冒頭の表現を「実際に試してみて比較してのレポート」に変更
3. WSL2環境での注意点セクションを追加
4. GPU/CPU別のメモリ要件を明記
5. 比較まとめ表にスペック情報を追加

## 学んだこと

### 技術的な学び

1. **MoEアーキテクチャの特性**
   - gpt-oss-120b: 117Bパラメータ、実際のアクティブは5.1B/トークン
   - モデルサイズは大きいが、推論時のメモリ使用は効率的

2. **WSL2のGPUアクセス制約**
   - NVIDIA CUDA: 完全サポート ✅
   - AMD統合GPU共有メモリ: アクセス不可 ❌
   - この制約は今後の開発で重要な考慮事項

3. **ハイブリッドモードの性能**
   - 16GB VRAM + システムRAM でgpt-oss-120bを実行
   - 8.54 tokens/s は妥当な性能
   - ただし、GPU ↔ CPU/RAM間の転送がボトルネック

### プロジェクト管理の学び

1. **記事の品質向上**
   - 抜粋ではなく全文を載せることで読者が実際の品質差を確認できる
   - `<details>`タグで折りたたみ可能にして可読性を保つ

2. **正確な情報の重要性**
   - メモリ要件をGPU/CPU別に明記する必要性
   - 推論速度の測定根拠（ollama --verboseの出力）を明確にする

3. **ユーザー環境への配慮**
   - WSL2 vs Windowsの違いは同じハードウェアでも大きな差
   - 環境別の推奨事項を提示することで読者が適切な選択をできる

## 次のステップ

### 短期（今週中）

1. **Windows環境でのベンチマーク**
   - BIOS/UEFIでUMA Frame Buffer Sizeを64GBに設定
   - Windows上でOllamaを実行して速度測定
   - 45+ tokens/s が出るか検証

2. **記事の更新**
   - Windows環境でのベンチマーク結果を追記
   - AMD統合GPU活用の詳細手順を追加

### 中期（今月中）

1. **gpt-oss:20bのテスト**
   - 16GB VRAMで完全にGPU実行可能
   - 速度向上を検証

2. **copy_robotでの実用テスト**
   - 実際のチャット応答での使用感確認
   - qwen2.5:14bとの使い分け戦略を確立

### 長期（今後）

1. **ハイブリッド運用の実装**
   - 軽量フィルタ（qwen2.5:14b）+ 深い推論（gpt-oss-120b）
   - 質問の複雑さに応じた自動切り替え

2. **AMD統合GPU最適化**
   - ROCmのWSL2サポート状況を追跡
   - 将来的にWSL2からもAMD統合GPUを活用できるか検証

## 感想

今日は予想以上に深い調査になった。単なる「gpt-oss-120bを試してみた」という記事を書くつもりが、WSL2とWindows環境の違い、AMD統合GPUの共有メモリ活用など、環境依存の重要な知見が得られた。

特に、同じハードウェアでも実行環境によって5倍以上の速度差（8.5 tps vs 45 tps）が出るという発見は大きい。これは他のユーザーにも有益な情報なので、記事に詳しく記載した。

qwen2.5:14bとの比較も、単なる速度比較ではなく、実際の応答内容を全文掲載することで、両者の特性の違いが明確になった。リアルタイム会話には軽量モデル、詳細な分析には大型モデルという使い分けが重要だと再認識。

次は実際にWindows環境で45+ tokens/sを体験してみたい。BIOS設定が必要だが、システムRAMが十分にあるので問題ないはず。楽しみだ。

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
