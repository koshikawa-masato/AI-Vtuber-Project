---
title: OpenAIのgpt-oss-120bをOllamaで試してみた【速報】
tags:
  - AI
  - LLM
  - OpenAI
  - Ollama
  - gpt-oss
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

## はじめに

OpenAIが2025年8月にオープンウェイトモデル「gpt-oss」をリリースしました。今回は120Bパラメータ版の `gpt-oss:120b` をOllamaで試してみたので、速報的にレポートします。

## gpt-oss-120bの特徴

### 基本スペック

- **パラメータ数**: 117B（実際のアクティブは5.1B/トークン）
- **アーキテクチャ**: Mixture-of-Experts (MoE)
- **ライセンス**: Apache 2.0（商用利用可能）
- **動作環境**: 単一80GB GPU（H100, MI300Xなど）

### 際立った特徴

1. **推論過程の可視化**
   - Chain-of-Thoughtによる思考プロセスが見える
   - デバッグやトラストが容易

2. **推論レベルの調整**
   - low / medium / high の3段階
   - システムメッセージで簡単に設定可能

3. **エージェント機能**
   - 関数呼び出し
   - Web検索（Ollamaが対応予定）
   - Python実行
   - 構造化出力

## Ollamaで試してみた

### インストール

```bash
ollama pull gpt-oss:120b
```

ダウンロードサイズは約65GB。10GbE環境で約6分でダウンロード完了しました。

### 実際に使ってみた

自作のAI VTuberチャットシステム「コピーロボット」で、キャラクター「牡丹」との会話に使ってみました。

![gpt-oss-120bでの会話例](https://github.com/koshikawa-masato/AI-Vtuber-Project/blob/main/screenshots/run_copy_robot_gpt-oss-120b.jpg?raw=true)

### 思考プロセスのフィルタリング

gpt-oss-120bは以下の形式で出力します：

```
Thinking...
[内部思考プロセス]
...done thinking.

[実際の応答]
```

この「Thinking...」部分は開発には有用ですが、エンドユーザーには不要なので、以下のようにフィルタリングしました：

```python
# 出力から思考部分を除去
if response.startswith('Thinking...'):
    thinking_end = response.find('...done thinking.')
    if thinking_end != -1:
        response = response[thinking_end + len('...done thinking.'):].strip()
```

### 応答速度

- **環境**: WSL2 Ubuntu 24.04
- **応答時間**: 12〜46秒/応答
- **推論速度**: 約8.5 tokens/s

120Bモデルとしては妥当な速度です。より速い応答が必要な場合は `gpt-oss:20b` も選択肢になります。

## 感想

### Good

- ✅ オープンソースで商用利用可能（Apache 2.0）
- ✅ 日本語の応答品質が高い
- ✅ 単一GPUで動作する設計
- ✅ 推論過程が見えるのは開発に便利

### 注意点

- ⚠️ モデルサイズが65GBと大きい
- ⚠️ 応答速度は小型モデルに比べて遅い
- ⚠️ 80GB GPUが推奨（CPUでも動くが実用的ではない）

## まとめ

OpenAIのgpt-oss-120bは、オープンウェイトながら高品質な推論モデルです。特に以下のようなユースケースに適しています：

- 推論過程の可視化が重要なアプリケーション
- エージェント的なタスク（関数呼び出し、ツール利用）
- 商用利用が必要なプロジェクト

Ollamaで簡単に試せるので、興味のある方はぜひ触ってみてください。

## 参考資料

- [OpenAI: Introducing gpt-oss](https://openai.com/index/introducing-gpt-oss/)
- [Ollama: gpt-oss-120b](https://ollama.com/library/gpt-oss:120b)
- [GitHub: openai/gpt-oss](https://github.com/openai/gpt-oss)
- [arXiv: gpt-oss-120b Model Card](https://arxiv.org/abs/2508.10925)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
