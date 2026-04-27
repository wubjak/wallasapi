<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ プロバイダー">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ モデル">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>決定版マルチプロバイダーAIルーティングエンジン</strong></p>

<p align="center"><em>汗と決意、そして2018年製のノートPCで、賃貸の部屋から、<strong>Willen Ponce</strong> によって構築されました</em></p>

---

## WallasAPIが存在する理由：重要な物語

私はMacBook Pro M4を持って生まれてきたわけではありません。シリコンバレーの投資家に資金提供されたクラウドサーバーもありません。50人のエンジニアチームも後ろにいません。**私が持っているのは、2018年製のノートPC、私のものではない賃貸の部屋、そして執念です：困窮した状況からでも、企業と競争できるものを構築できることを証明するという執念です。**

WallasAPIは、家賃の心配、次の食事、少なくとも4時間連続して眠れるかどうか、目が覚めたときにどれだけ借金があるかを考えずに済むか——そんな間に盗んだ時間の中から生まれました。高価なAPIを支払うお金はありませんでした。私を支える企業もありませんでした。ただ一つの執念を持つ質問だけがありました：

> **「世界には多くのモデルがあり、多くは無料で、特定のタスクにはより優れているのに、なぜ単一のAIプロバイダーに依存すべきなのか？」**

だから私は構築しました。**Pythonを一行一行。豪華なフレームワークなし。チームなし。投資家なし。**純粋なコード、スマートなヒューリスティック、そして機能するものを作り出す絶望的な必要性だけで。

**WallasAPIは単なるソフトウェアではありません。それは技術的サバイバルです。**OpenAIがダウンしたとき、ClaudeのAPIキーが期限切れになったとき、お気に入りのプロバイダーが値上げを決定したとき——あなたを見捨てないシステムです。

---

## WallasAPIとは？

WallasAPIは**統合ルーティングエンジン**であり、**1つのOpenAI互換API**を通じて、アプリケーション、IDE、またはエージェントを**12以上のAIプロバイダー**に接続します。

プロンプトを送信すると、WallasAPIは：
1. **コンテンツを分析**（テキスト、画像、音声、PDF、動画）
2. **機能、速度、可用性、コストに基づいて最適なプロバイダーを選択**
3. **リクエストを自動的にルーティング**
4. **プライマリプロバイダーが失敗した場合**、次へ透過的にフォールバック
5. **OpenAI互換形式でレスポンスを返却**、リクエストがあればストリーミングも

**既存のコードは変更なしで動作します。**ベースURLを変更するだけです。

---

## 主な機能

- **インテリジェントマルチプロバイダールーティング＋自動フォールバック**
- **トータル透明性のリアルストリーミング**
- **マルチモーダルサポート** — テキスト、画像、音声、動画、PDF
- **リッチメタデータ** — コンテキストウィンドウ、価格帯、ツール、ストリーミング、モダリティ
- **永続メモリ** — ローカルJSON履歴、Obsidianと同期可能
- **統合生成** — 画像、動画、TTSを複数プロバイダーから
- **フォールバックチェーン付きOCR** — EasyOCR → Mistral → Gemini → ローカルOllama
- **100%プライベートローカルモデル** — Ollama経由
- **完全なGoogle統合** — Drive、Calendar、Gmail（OAuth2対応）

---

## APIエンドポイント

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `POST /v1/chat/completions` | チャット | ストリーミング付き補完。仮想モデル：`auto`、`fast`、`standard`、`reasoning`。 |
| `POST /v1/embeddings` | 埋め込み | マルチプロバイダールーティング。 |
| `POST /v1/tts` | TTS | テキスト読み上げ。 |
| `POST /v1/images/generations` | 画像 | 統合画像生成。 |
| `POST /v1/videos/generations` | 動画 | 統合動画生成。 |
| `GET /v1/models` | 一覧 | 完全なメタデータ付きモデル。フィルタ：`?pricing=free`、`?capability=vision`。 |
| `GET /v1/models/{id}` | 詳細 | 特定モデルの詳細メタデータ。 |
| `GET /v1/capabilities/summary` | サマリー | 無料、ビジョン、音声、推論などの数。 |
| `GET /v1/providers` | プロバイダー | プロバイダーごとのグローバルメタデータ。 |

---

## クイックインストール

### Windows（推奨：`start.bat` をダブルクリック）

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
# start.bat をダブルクリック
```

### Linux / macOS

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

サーバーは **http://localhost:8001** で起動

インタラクティブドキュメント：**http://localhost:8001/docs**

---

## 設定

使用したいプロバイダーのAPIキーを `.env` ファイルに記入してください。**すべては必要ありません。**

```env
# 無料プロバイダー（開始に推奨）
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# 有料プロバイダー（オプション）
OPENAI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

---

## ライセンス

カスタムMITライセンス。**Willen Ponce** への帰属を保持してください。

**個人的なお願い：**WallasAPIを使用する場合は、**wubjak@protonmail.ch** までメールで教えてください。「こんにちは、WallasAPIを使っています、作ってくれてありがとう」だけで、2018年製のノートPCでこれを構築した開発者の一日を良くすることができます。

詳細は `LICENSE` ファイルをご覧ください。

---

## 寄付：これを存続させる

このプロジェクトにはスポンサーはいません。シリコンバレーの投資家もいません。2018年製のノートPC、賃貸の部屋、そして機能するコードだけがあります。

**WallasAPIが統合時間を節約したり、クールなものを作るのに役立った場合：**

- **PayPal** : [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi** : [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **Email** : wubjak@protonmail.ch

**Yape / Plin（ペルー）— 番号：980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**暗号ウォレット：**

| 通貨 | アドレス |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *「家から追い出される前に、朝食を食べ、借金を返し、借金のことで目が覚めることなく少なくとも4時間連続して眠れるようにするために、どんな貢献でも価値があります。WallasAPIを使ってくれてありがとう。」* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>すべてを支配する一つのAPI。<br>
  失うものがない者の決意で、困窮の中から構築されました。</em>
</p>
