# arXiv検索ツール利用ガイド

## 概要

このツールは、arXivから論文を検索し、データベースに保存したり、PDFをダウンロードしたりする機能を提供します。

## 基本的な使い方

```bash
python scripts/search_prompt_engineering.py "検索キーワード" [オプション]
```

## 主な機能

1. **キーワード検索**: 指定したキーワードでarXiv論文を検索
2. **カテゴリフィルタリング**: 特定の研究分野に絞り込み
3. **柔軟な期間指定**: 相対期間や具体的な日付範囲で絞り込み
4. **検索結果の並べ替え**: 関連性、更新日、投稿日などでソート
5. **PDFダウンロード**: 検索結果の論文PDFを自動ダウンロード
6. **データベース保存**: 検索結果をローカルデータベースに保存

## オプション一覧

### 基本オプション

| オプション | 説明 |
|------------|------|
| `[キーワード]` | 検索キーワード（デフォルト: "prompt engineering"） |
| `-h, --help` | ヘルプメッセージの表示 |
| `-c, --category` | arXivカテゴリでフィルタリング（例: cs.AI） |
| `-l, --list-categories` | 利用可能なカテゴリ一覧を表示 |

### 期間指定オプション

| オプション | 説明 |
|------------|------|
| `-P, --period` | 相対的な期間指定（例: 3d, 2w, 6m, 1y） |
| `-dr, --date-range` | 日付範囲指定（例: 2023-01-01~2024-01-01） |
| `-f, --from-date` | 開始日指定（YYYY-MM-DD形式） |
| `-t, --to-date` | 終了日指定（YYYY-MM-DD形式） |

### 期間プリセット

| オプション | 説明 |
|------------|------|
| `--last-week` | 過去1週間 |
| `--last-month` | 過去1ヶ月 |
| `--last-3-months` | 過去3ヶ月 |
| `--last-6-months` | 過去6ヶ月 |
| `--last-year` | 過去1年 |

### ソートオプション

| オプション | 説明 |
|------------|------|
| `-s, --sort-by` | ソート基準（relevance, lastUpdatedDate, submittedDate） |
| `-o, --sort-order` | ソート順序（ascending, descending） |

### PDFダウンロードオプション

| オプション | 説明 |
|------------|------|
| `-d, --download-pdf` | 論文PDFをダウンロード |
| `-m, --max-downloads` | ダウンロードする最大数（デフォルト: 10、0で全件） |
| `-p, --parallel` | 並列ダウンロード数（デフォルト: 3） |

### データベースオプション

| オプション | 説明 |
|------------|------|
| `--skip-db` | データベースへの保存をスキップ |

## 使用例

### 基本的な検索

```bash
python scripts/search_prompt_engineering.py "large language model"
```

### カテゴリを指定して検索

```bash
python scripts/search_prompt_engineering.py "prompt engineering" --category cs.AI
```

### 過去3ヶ月の論文を検索

```bash
python scripts/search_prompt_engineering.py "generative ai" --last-3-months
```

### カスタム期間指定（過去45日間）

```bash
python scripts/search_prompt_engineering.py "diffusion model" --period 45d
```

### 特定の日付範囲で検索

```bash
python scripts/search_prompt_engineering.py "transformers" --date-range 2024-01-01~2024-04-30
```

### 関連性順にソート

```bash
python scripts/search_prompt_engineering.py "nlp" --sort-by relevance
```

### 検索結果のPDFをダウンロード

```bash
python scripts/search_prompt_engineering.py "graph neural networks" --download-pdf
```

### すべての検索結果のPDFをダウンロード

```bash
python scripts/search_prompt_engineering.py "foundation models" --download-pdf --max-downloads 0
```

### データベースに保存せずPDFのみダウンロード

```bash
python scripts/search_prompt_engineering.py "multimodal learning" --download-pdf --skip-db
```

## 注意事項

- arXiv APIには使用制限があるため、短時間に大量のリクエストを行うと一時的にブロックされる可能性があります
- 大量の論文PDFをダウンロードする場合は、サーバーの負荷を考慮して適切な間隔を空けることをお勧めします
- ダウンロードしたPDFは `data/pdfs` ディレクトリに保存されます
- 検索結果はSQLiteデータベース（`data/arxiv_papers.db`）に保存されます
