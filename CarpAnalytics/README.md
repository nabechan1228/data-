# NPB Insight Pro

プロ野球（NPB）12球団の全選手データを集約し、ポテンシャル（将来性）と現実の実績を可視化・分析するモダンなウェブアプリケーションです。

## 🌟 主な機能

### 1. 全12球団・1,000名以上の選手データベース
- セ・リーグ、パ・リーグすべての支配下・育成選手データを網羅。
- ポジション別、球団別フィルタリング機能。

### 2. ポテンシャル・マトリクス分析
- 横軸：現在の実績（Current Performance）
- 縦軸：将来性（Potential Ceiling）
- 散布図により、どの選手が「完成されたベテラン」か「将来有望な若手」かを一目で判別可能。

### 3. 今年度1軍成績のリアルタイム表示
- NPB公式サイトから最新の打者・投手成績を自動取得。
- 打率、本塁打、防御率、奪三振などの主要スタッツを選手カードに表示。
- 1軍出場選手には「1軍」バッジを付与。

### 4. 毎日自動アップデート機能
- 毎日午前5:00（JST）に自動スクレイピングを実行。
- 前日の試合結果を反映した最新データで分析が可能。

### 5. セキュリティ & パフォーマンス
- レート制限（SlowAPI）によるDoS対策。
- 厳格な入力バリデーション（Pydantic v2）。
- Content Security Policy (CSP) によるXSS対策。
- BeautifulSoupによる高速な解析処理。

## 🛠 技術スタック

### バックエンド
- **言語**: Python 3.12+
- **フレームワーク**: FastAPI
- **データベース**: SQLite3
- **タスク管理**: APScheduler (自動更新用)
- **スクレイピング**: BeautifulSoup4, Requests

### フロントエンド
- **言語**: JavaScript (ES6+)
- **フレームワーク**: React 18
- **ビルドツール**: Vite
- **チャート**: Recharts
- **アイコン**: Lucide React
- **スタイル**: Vanilla CSS (Custom Design System)

## 🚀 セットアップ

### バックエンド
1. 仮想環境の作成と有効化
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. 依存関係のインストール
   ```bash
   pip install fastapi uvicorn beautifulsoup4 requests pandas slowapi python-dotenv apscheduler
   ```
3. 環境変数の設定
   `.env` ファイルを作成し、以下を設定
   ```env
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
   SCRAPE_SECRET_TOKEN=your_secure_token_here
   ```
4. サーバーの起動
   ```bash
   uvicorn main:app --reload --port 8001
   ```

### フロントエンド
1. 依存関係のインストール
   ```bash
   npm install
   ```
2. 開発サーバーの起動
   ```bash
   npm run dev
   ```

## 🔒 セキュリティ対策
- **API Token**: データの破壊的な更新（スクレイピング再実行など）には、`X-Request-Token` ヘッダーによる認証が必須です。
- **Rate Limiting**: IPアドレスごとにリクエスト回数を制限し、リソースの枯渇を防ぎます。
- **Data Validation**: 選手名や球団名のクエリには厳格な正規表現とホワイトリストバリデーションを適用しています。

## 📝 ライセンス
本プロジェクトは学習および個人利用を目的としています。データソースであるNPB公式サイトの利用規約を遵守してください。
