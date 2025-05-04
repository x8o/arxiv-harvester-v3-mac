# arXiv Harvester v3 - ユーザーガイド

## 目次

1. [概要](#概要)
2. [システム要件](#システム要件)
3. [インストール](#インストール)
4. [基本的な使い方](#基本的な使い方)
   - [コマンドラインから実行](#コマンドラインから実行)
   - [Pythonライブラリとして使用](#pythonライブラリとして使用)
5. [設定オプション](#設定オプション)
   - [検索パラメータ](#検索パラメータ)
   - [スケジュール設定](#スケジュール設定)
   - [Slack通知](#slack通知)
6. [データベース管理](#データベース管理)
7. [トラブルシューティング](#トラブルシューティング)

## 概要

arXiv Harvester v3は、arXiv.orgから学術論文を自動的に検索、取得、保存し、新しい論文が見つかった際にSlackで通知するPythonアプリケーションです。テスト駆動開発（TDD）の原則に従って開発され、拡張性と信頼性を重視しています。

## システム要件

- Python 3.9以上
- SQLite3
- インターネット接続（arXiv APIへのアクセス用）
- Slack webhook URL（通知機能を使用する場合）

## インストール

### GitHubからのインストール

```bash
# リポジトリをクローン
git clone https://github.com/x8o/arxiv-harvester-v3-mac.git
cd arxiv-harvester-v3-mac

# パッケージとして開発モードでインストール
pip install -e .
```

### 依存関係の確認

インストールが正常に完了したことを確認するために、以下のコマンドを実行してテストを走らせることができます：

```bash
python -m pytest
```

すべてのテストが通過すれば、正常にインストールされています。

## 基本的な使い方

arXiv Harvesterは、コマンドラインツールとしても、Pythonライブラリとしても使用できます。

### コマンドラインから実行

以下のコマンドでハーベスターを実行できます：

```bash
# デフォルト設定で実行（設定ファイルがあれば読み込み）
python -m arxiv_harvester.run

# 検索パラメータを指定して実行
python -m arxiv_harvester.run --query "quantum computing" --categories quant-ph,cs.AI

# スケジュールを無視して強制実行
python -m arxiv_harvester.run --force-run

# 状態ファイルを指定して実行
python -m arxiv_harvester.run --state-file "path/to/state.json"
```

### Pythonライブラリとして使用

Pythonスクリプト内でarXiv Harvesterを使用する基本的な例：

```python
from arxiv_harvester.api.client import ArxivApiClient
from arxiv_harvester.store.database import DatabaseManager
from arxiv_harvester.notify.slack import SlackNotifier
from arxiv_harvester.scheduler.scheduler import Scheduler

# コンポーネントの初期化
api_client = ArxivApiClient()
db_manager = DatabaseManager("papers.db")
db_manager.initialize_database()
notifier = SlackNotifier()

# ハーベスト処理の設定と実行
scheduler = Scheduler(api_client, db_manager, notifier)
scheduler.set_search_parameters(
    query="機械学習 深層学習",  # 検索クエリ
    categories=["cs.AI", "cs.LG"],  # カテゴリ（複数指定可能）
    max_results=50  # 最大結果数
)
scheduler.set_slack_webhook("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
scheduler.run_harvest()
```

## 設定オプション

### 検索パラメータ

arXiv Harvesterでは、以下の検索パラメータを設定できます：

- **クエリ（query）**: 検索したいキーワードや論文のタイトル、著者名など
- **カテゴリ（categories）**: 論文のカテゴリ（例：`cs.AI`=人工知能、`quant-ph`=量子物理学）
- **最大結果数（max_results）**: 一度に取得する最大論文数

#### 有効なarXivカテゴリの例：

- **コンピュータサイエンス**: cs.AI（人工知能）, cs.CL（計算言語学）, cs.LG（機械学習）, cs.CV（コンピュータビジョン）
- **物理学**: physics.acc-ph（加速器物理学）, physics.ao-ph（大気海洋物理学）, quant-ph（量子物理学）
- **数学**: math.AC（可換代数）, math.AG（代数幾何学）
- **統計学**: stat.ML（機械学習）, stat.TH（統計理論）

### スケジュール設定

ハーベスト処理の実行頻度を設定できます：

```python
# 毎日実行
scheduler.set_schedule("daily")

# 毎週実行（デフォルト）
scheduler.set_schedule("weekly")

# 毎月実行
scheduler.set_schedule("monthly")
```

### Slack通知

Slack通知のカスタマイズ：

```python
# 通知設定
notifier = SlackNotifier()

# 重要なカテゴリを設定（これらのカテゴリの論文は強調表示されます）
notifier.set_important_categories(["cs.AI", "quant-ph"])

# Markdownフォーマットを有効化
notifier.set_use_markdown(True)

# リッチフォーマット（ブロック）での通知
scheduler.send_notifications(papers, use_blocks=True)
```

## データベース管理

arXiv Harvesterは論文メタデータをSQLiteデータベースに保存します。データベースの操作例：

```python
from arxiv_harvester.store.database import DatabaseManager

# データベースの初期化
db = DatabaseManager("papers.db")
db.initialize_database()

# 最新の論文を取得（最大5件）
recent_papers = db.get_recent_papers(5)

# カテゴリ別の論文数
category_counts = db.count_papers_by_category()
print(category_counts)  # {'cs.AI': 42, 'cs.LG': 31, ...}

# 日付範囲での検索
from datetime import datetime
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)
papers_2023 = db.get_papers_by_date_range(start_date, end_date)

# 著者による検索
einstein_papers = db.get_papers_by_author("Einstein")

# キーワード検索
quantum_papers = db.search_papers(title_keyword="quantum", abstract_keyword="algorithm")

# データベースのバックアップ
db.backup_database("backup_2025-05-04.db")
```

## トラブルシューティング

### 一般的な問題

**Q: API接続エラーが発生する**

A: インターネット接続を確認してください。arXiv APIには公平使用ポリシーがあり、頻繁なリクエストは制限される場合があります。デフォルトのディレイ設定（3秒）を長くすることで解決する場合があります：

```python
# APIリクエスト間の待機時間を5秒に設定
api_client = ArxivApiClient(delay=5.0)
```

**Q: Slack通知が届かない**

A: 以下を確認してください：
1. Webhook URLが正しいこと
2. Webhookの統合がSlackワークスペースで有効になっていること
3. テスト通知を送信して動作確認する：

```python
notifier = SlackNotifier()
success = notifier.post_message_to_slack("テストメッセージ", "YOUR_WEBHOOK_URL")
print(success)  # Trueなら成功、Falseなら失敗
```

**Q: 同じ論文が繰り返し通知される**

A: これは`filter_new_papers`メソッドが正しく機能していない可能性があります。データベースが正しく初期化されていることを確認し、既存の論文IDがデータベースに存在するか確認してください。
