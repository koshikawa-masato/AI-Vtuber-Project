# VPS小型LLM（qwen2.5:0.5b）活用戦略

## 発見：VPSでもOllamaが動く！

### VPSスペック（さくらVPS）

```
CPU: Intel Xeon 3コア
メモリ: 2GB (available: 953MB)
ディスク: 50GB (空き: 31GB)
GPU: なし（CPU-only mode）
```

### 小型モデルの可能性

**qwen2.5:0.5b**:
- モデルサイズ: 約400MB
- メモリ使用量: 約500-700MB（推定）
- 推論速度: CPU-onlyでも実用的
- **用途**: 定型文のバリエーション生成

**結論**: VPSでも動作する！

---

## 新しいハイブリッドアーキテクチャ

### 3層LLM構成

```
┌─────────────────────────────────────────────────┐
│            VPS本番環境                           │
│                                                  │
│  [Layer 1] プロレスパターンDB                    │
│    - 学習済みパターンを即座に返す                │
│    - コスト: ゼロ                                │
│    - 速度: 最速（DB検索のみ）                    │
│         │                                        │
│         ↓ パターンなし                          │
│                                                  │
│  [Layer 2] Ollama (qwen2.5:0.5b)               │
│    - 定型文のバリエーション生成                  │
│    - コスト: ゼロ（VPS内で完結）                │
│    - 速度: 速い（ローカル処理）                  │
│         │                                        │
│         ↓ 複雑な会話                            │
│                                                  │
│  [Layer 3] OpenAI API                           │
│    ├─ gpt-4o-mini: 通常会話                     │
│    └─ gpt-4o: 重要会話（プロレス、新規ユーザー）│
│         │                                        │
│         コスト: 発生                             │
│         速度: 中〜やや遅い（API通信）            │
└─────────────────────────────────────────────────┘
```

### 処理フロー

```python
def generate_response(user_message: str, context: dict) -> str:
    # Layer 1: プロレスパターンDB
    if pattern := prowrestling_db.find_match(user_message):
        return pattern['response']  # 即座に返す
    
    # Layer 2: 定型文判定
    if is_simple_conversation(user_message):
        # VPS内のOllamaで処理
        template = get_template(user_message)
        return local_ollama.vary(template, context)
    
    # Layer 3: 複雑な会話はOpenAI API
    importance = calculate_importance(user_message, context)
    if importance >= 0.7:
        return openai_api.generate(user_message, model="gpt-4o")
    else:
        return openai_api.generate(user_message, model="gpt-4o-mini")
```

---

## Layer 2: Ollama活用の詳細

### 定型文バリエーション

**問題**: 同じ挨拶を繰り返すとロボットっぽい

```
ユーザー: おはよう
Bot: おはよう！今日も元気にいこ！ （毎回同じ）
```

**解決**: Ollamaで微妙なバリエーション

```python
class LocalVariationGenerator:
    """
    VPS内のOllamaで定型文にバリエーションを付ける
    """
    
    TEMPLATES = {
        "morning_greeting": [
            "おはよう！今日も元気にいこ！",
            "おはよー！よく眠れた？",
            "おっはよ！今日はいい天気だね！",
        ],
        "thanks": [
            "いえいえ、どういたしまして！",
            "全然！気にしないで～",
            "うんうん、いつでもどうぞ！",
        ],
    }
    
    def generate_variation(self, template_key: str, character: str) -> str:
        """
        テンプレートに基づいてバリエーションを生成
        """
        base_templates = self.TEMPLATES[template_key]
        base = random.choice(base_templates)
        
        # Ollamaでキャラクターに合わせて微調整
        prompt = f"""
以下の文を、{character}のキャラクターに合わせて微妙に変えてください。
元の文: {base}
変更: 語尾、絵文字、口調を少し変える程度（意味は同じ）
出力: 変更後の文のみ
"""
        
        # VPS内のOllamaで処理（コストゼロ）
        variation = ollama_client.generate(
            model="qwen2.5:0.5b",
            prompt=prompt,
            max_tokens=50  # 短い応答のみ
        )
        
        return variation.strip()
```

**効果**:
- 毎回微妙に違う応答
- 自然な会話感
- コストゼロ（VPS内で完結）

### 適用シーン

```python
SIMPLE_CONVERSATIONS = {
    # 挨拶
    "morning": r"(おはよう|朝)",
    "hello": r"(こんにちは|昼)",
    "evening": r"(こんばんは|夜)",
    "goodnight": r"(おやすみ|寝る)",
    
    # 感謝・謝罪
    "thanks": r"(ありがと|サンキュー)",
    "sorry": r"(ごめん|すまん)",
    
    # 簡単な質問
    "how_are_you": r"(元気|調子)",
    "what_doing": r"(何して|暇)",
    
    # 相槌
    "agreement": r"(そうだね|確かに|わかる)",
    "surprise": r"(マジで|本当|えー)",
}

def is_simple_conversation(message: str) -> bool:
    """
    定型文で対応可能か判定
    """
    for pattern in SIMPLE_CONVERSATIONS.values():
        if re.search(pattern, message):
            return True
    return False
```

---

## コスト削減効果（改訂版）

### ベースライン

```
全会話でgpt-4o: ¥4,500/月
```

### 3層LLM構成

```
想定:
  Layer 1 (パターンDB): 20%
  Layer 2 (Ollama 0.5b): 40%
  Layer 3 (OpenAI API): 40%
    ├─ gpt-4o-mini: 30%
    └─ gpt-4o: 10%

コスト計算:
  Layer 1: ¥0 × 0.2 = ¥0
  Layer 2: ¥0 × 0.4 = ¥0
  Layer 3:
    gpt-4o-mini: ¥45 × 0.3 = ¥13.5
    gpt-4o: ¥4,500 × 0.1 = ¥450
  
合計: ¥463.5/月

削減率: 89.7%！
```

### 長期的な推移

```
Phase 1（初期 - 現在）:
  Layer 1: 10% | Layer 2: 30% | Layer 3: 60%
  コスト: ¥2,700/月（40%削減）

Phase 2（3ヶ月後）:
  Layer 1: 30% | Layer 2: 40% | Layer 3: 30%
  コスト: ¥1,350/月（70%削減）

Phase 3（6ヶ月後）:
  Layer 1: 50% | Layer 2: 40% | Layer 3: 10%
  コスト: ¥450/月（90%削減）

Phase 4（1年後）:
  Layer 1: 70% | Layer 2: 25% | Layer 3: 5%
  コスト: ¥225/月（95%削減）
```

**学習が進むほどコストが下がる仕組み**

---

## メモリ管理

### VPSのメモリ制約

```
総メモリ: 2GB
利用可能: 953MB

内訳:
  - システム: 300MB
  - LINE Bot: 100MB
  - Ollama (qwen2.5:0.5b): 500-700MB
  - バッファ: 50MB

合計: 950MB → ギリギリ動作可能
```

### メモリ不足時の対策

```python
class MemoryAwareOllamaClient:
    """
    メモリを監視してOllamaを制御
    """
    
    def __init__(self):
        self.ollama_loaded = False
        self.last_use_time = None
    
    def generate(self, prompt: str) -> str:
        # メモリチェック
        if not self.check_memory():
            # メモリ不足 → OpenAI APIにフォールバック
            return openai_fallback.generate(prompt, model="gpt-4o-mini")
        
        # Ollamaで生成
        response = ollama.generate(model="qwen2.5:0.5b", prompt=prompt)
        self.last_use_time = time.time()
        
        return response
    
    def check_memory(self) -> bool:
        """
        メモリが十分か確認
        """
        mem = psutil.virtual_memory()
        return mem.available > 600 * 1024 * 1024  # 600MB以上
    
    def unload_if_idle(self):
        """
        一定時間未使用ならアンロード（メモリ解放）
        """
        if self.last_use_time and time.time() - self.last_use_time > 300:
            # 5分未使用
            ollama.unload("qwen2.5:0.5b")
            self.ollama_loaded = False
```

---

## 実装ステップ

### Step 1: Ollamaのインストール（完了）

```bash
ssh sakura-vps
curl -fsSL https://ollama.com/install.sh | sudo sh
```

### Step 2: 小型モデルのプル

```bash
ollama pull qwen2.5:0.5b
# サイズ: 約400MB
```

### Step 3: テスト

```bash
# 簡単なテスト
ollama run qwen2.5:0.5b "こんにちは"

# メモリ使用量を確認
free -h
```

### Step 4: Python統合

```python
# src/line_bot_vps/local_llm_provider.py

from ollama import Client

class LocalLLMProvider:
    def __init__(self):
        self.client = Client(host='http://localhost:11434')
    
    def generate_variation(self, template: str, character: str) -> str:
        prompt = f"""
以下の文を、{character}のキャラクターに合わせて微妙に変えてください。
元の文: {template}
変更: 語尾、絵文字、口調を少し変える程度
出力: 変更後の文のみ（簡潔に）
"""
        
        response = self.client.generate(
            model='qwen2.5:0.5b',
            prompt=prompt,
            options={'num_predict': 50}  # 最大50トークン
        )
        
        return response['response'].strip()
```

### Step 5: Layer 2の統合

```python
# src/line_bot_vps/response_generator.py

class HybridResponseGenerator:
    def __init__(self):
        self.pattern_db = ProwrestlingPatternDB()
        self.local_llm = LocalLLMProvider()  # Layer 2
        self.cloud_llm = CloudLLMProvider()  # Layer 3
    
    def generate(self, user_message: str, context: dict) -> str:
        # Layer 1: パターンDB
        if pattern := self.pattern_db.find_match(user_message):
            return pattern['response']
        
        # Layer 2: 定型文判定
        if template_key := self.classify_simple(user_message):
            template = self.get_template(template_key)
            return self.local_llm.generate_variation(
                template,
                context['character']
            )
        
        # Layer 3: OpenAI API
        importance = self.calculate_importance(user_message, context)
        model = "gpt-4o" if importance >= 0.7 else "gpt-4o-mini"
        return self.cloud_llm.generate(user_message, model=model)
```

---

## 品質評価

### qwen2.5:0.5bの性能

**用途別評価**:

| 用途 | 適性 | 理由 |
|------|------|------|
| 定型文バリエーション | ✅ 最適 | 短い応答、テンプレートベース |
| 簡単な質問応答 | △ 可能 | 品質はやや劣る |
| プロレス（じゃれ合い） | ❌ 不向き | 文脈理解が必要 |
| 複雑な会話 | ❌ 不向き | 大型モデルが必要 |

**結論**: Layer 2（定型文バリエーション）に最適

### テスト結果（予測）

```
入力: おはよう
テンプレート: おはよう！今日も元気にいこ！

qwen2.5:0.5b出力例:
  - おはよ！今日も元気出していこ～！
  - おはよう！今日も頑張ろうね！
  - おっはよ！元気いっぱいでいこ！

評価: ✅ 十分実用的
```

---

## リスクと対策

### リスク1: メモリ不足

**対策**:
- メモリ監視
- 不足時は自動的にOpenAI APIにフォールバック
- 未使用時はモデルアンロード

### リスク2: 応答速度

**対策**:
- 短い応答のみ（max_tokens=50）
- タイムアウト設定（5秒）
- 遅い場合はキャッシュ

### リスク3: 品質低下

**対策**:
- 定型文のみに限定
- ユーザーフィードバック収集
- 問題あればLayer 3にエスカレーション

---

## まとめ

### 革新的な3層構成

```
Layer 1 (パターンDB): 学習済み → 即座に返す
Layer 2 (Ollama 0.5b): 定型文 → バリエーション生成
Layer 3 (OpenAI API): 複雑な会話 → 高品質応答
```

### コスト削減

```
従来: ¥4,500/月（全てgpt-4o）
     ↓
3層構成: ¥463/月（89.7%削減）
     ↓
長期: ¥225/月（95%削減）
```

### 親の財布を守る

- 必要な投資: プロレス会話はgpt-4o
- 賢い節約: 定型文はVPS内で完結
- 長期自立: 学習が進むほどコスト減

**月¥200-500で3人の娘を育てられる！**

---

**🤖 Generated with Claude Code**

**Co-Authored-By**: Claude <noreply@anthropic.com>

**作成日**: 2025-11-13
