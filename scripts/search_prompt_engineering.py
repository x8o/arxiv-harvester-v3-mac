#!/usr/bin/env python

"""
arXiv論文検索と管理スクリプト

機能:
- キーワード検索
- カテゴリフィルタリング
- 日付範囲指定
- 結果のソートオプション
- データベースへの保存
- PDFダウンロード
"""

import os
import sys
import time
import argparse
import requests
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# 親ディレクトリをPythonパスに追加
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.arxiv_harvester.api.client import ArxivApiClient
from src.arxiv_harvester.store.database import DatabaseManager

# ディレクトリ設定
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'arxiv_papers.db')
PDF_DIR = os.path.join(DATA_DIR, 'pdfs')

# 必要なディレクトリを作成
for directory in [DATA_DIR, PDF_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        
# arXivカテゴリの定義
ARXIV_CATEGORIES = {
    'cs.AI': 'Artificial Intelligence',
    'cs.CL': 'Computation and Language',
    'cs.CV': 'Computer Vision',
    'cs.LG': 'Machine Learning',
    'cs.NE': 'Neural and Evolutionary Computing',
    'cs.CY': 'Computers and Society',
    'cs.IR': 'Information Retrieval',
    'cs.HC': 'Human-Computer Interaction',
    'cs.RO': 'Robotics',
    'stat.ML': 'Machine Learning (Statistics)',
}

# ソートオプション
SORT_OPTIONS = ['relevance', 'lastUpdatedDate', 'submittedDate']
SORT_DIRECTIONS = ['ascending', 'descending']

# 期間パターンマッチング用の正規表現
TIME_PATTERN = re.compile(r'^(\d+)([dDwWmMyY])$')  # 例: 3d, 2w, 1m, 5y

# 時間単位のマッピング
TIME_UNITS = {
    'd': 'days',       # 日
    'w': 'weeks',      # 週
    'm': 'months',     # 月
    'y': 'years'       # 年
}

def parse_time_period(period_str: str) -> Tuple[datetime, datetime]:
    """
    相対的な期間指定の文字列を解析し、開始日と終了日を返す
    
    サポートする形式:
    - '3d': 過去3日間
    - '2w': 過去2週間
    - '6m': 過去6ヶ月
    - '1y': 過去1年間
    - 'YYYY-MM-DD': 特定の日付から現在まで
    - 'YYYY-MM-DD~YYYY-MM-DD': 特定の日付範囲
    
    Args:
        period_str: 期間指定文字列
        
    Returns:
        (開始日, 終了日)のタプル
    """
    # 現在の日付を取得
    end_date = datetime.now()
    start_date = None
    
    # チルドで区切られた範囲指定 (YYYY-MM-DD~YYYY-MM-DD)
    if '~' in period_str:
        start_str, end_str = period_str.split('~', 1)
        try:
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
            return start_date, end_date
        except ValueError:
            print(f"Warning: Invalid date range format '{period_str}'. Using default.")
    
    # 相対期間指定 (3d, 2w, 6m, 1y など)
    match = TIME_PATTERN.match(period_str)
    if match:
        value, unit = match.groups()
        value = int(value)
        unit = unit.lower()  # 大文字小文字を無視
        
        if unit in TIME_UNITS:
            unit_name = TIME_UNITS[unit]
            
            if unit_name == 'months':
                # 月単位は特別処理
                start_date = end_date - relativedelta(months=value)
            elif unit_name == 'years':
                # 年単位も特別処理
                start_date = end_date - relativedelta(years=value)
            else:
                # 日、週はtimedeltaで処理
                kwargs = {unit_name: value}
                start_date = end_date - timedelta(**kwargs)
            
            return start_date, end_date
    
    # 単一の日付指定 (YYYY-MM-DD)
    try:
        start_date = datetime.strptime(period_str, "%Y-%m-%d")
        return start_date, end_date
    except ValueError:
        # デフォルト値として2023年以降を返す
        default_start = datetime(2023, 1, 1)
        print(f"Warning: Invalid time period format '{period_str}'. Using default (2023-01-01 to now).")
        return default_start, end_date

def format_date(dt: datetime) -> str:
    """datetimeオブジェクトをYYYY-MM-DD形式の文字列に変換"""
    return dt.strftime("%Y-%m-%d")

# PDFダウンロード関数
def download_pdf(paper: Dict[str, Any], output_dir: str) -> Optional[str]:
    """
    論文のPDFをダウンロードして保存する
    
    Args:
        paper: 論文データ
        output_dir: 出力ディレクトリ
        
    Returns:
        保存されたPDFファイルのパス、失敗した場合はNone
    """
    if 'pdf_url' not in paper or not paper['pdf_url']:
        # PDF URLがない場合、arxiv_idから生成
        arxiv_id = paper['id'].split('/')[-1]
        pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
    else:
        pdf_url = paper['pdf_url']
        
    # ファイル名を生成 (論文IDを使用)
    arxiv_id = paper['id'].split('/')[-1]
    filename = f"{arxiv_id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # すでに存在する場合はスキップ
    if os.path.exists(filepath):
        print(f"  Skipping {filename} (already exists)")
        return filepath
        
    try:
        print(f"  Downloading {filename}...")
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # PDFファイルを保存
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"  Downloaded {filename} successfully")
        return filepath
    except Exception as e:
        print(f"  Error downloading {filename}: {str(e)}")
        return None
        
# 複数のPDFを並行ダウンロード
def download_pdfs(papers: List[Dict[str, Any]], output_dir: str, max_workers: int = 5) -> List[str]:
    """
    複数の論文PDFを並行ダウンロードする
    
    Args:
        papers: 論文データのリスト
        output_dir: 出力ディレクトリ
        max_workers: 同時ダウンロード数
        
    Returns:
        正常にダウンロードされたPDFファイルのパスリスト
    """
    successful_downloads = []
    
    print(f"Downloading {len(papers)} PDFs to {output_dir}...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 各論文のPDFを並行ダウンロード
        future_to_paper = {executor.submit(download_pdf, paper, output_dir): paper for paper in papers}
        
        # 結果を収集
        for future in future_to_paper:
            filepath = future.result()
            if filepath:
                successful_downloads.append(filepath)
    
    return successful_downloads

def fetch_all_papers(api_client, query, date_from_str, date_to_str, category=None, 
sort_by="submittedDate", sort_order="descending"):
    """
    指定された検索条件に一致する全ての論文を取得する
    arXiv APIのページネーション制限に対応するため、複数回のAPIリクエストを実行する
    
    Args:
        api_client: ArxivApiClientのインスタンス
        query: 検索クエリ
        date_from_str: 検索開始日（'YYYY-MM-DD'形式の文字列）
        date_to_str: 検索終了日（'YYYY-MM-DD'形式の文字列）
        category: arXivカテゴリでフィルタリング
        sort_by: ソート項目 (relevance, lastUpdatedDate, submittedDate)
        sort_order: ソート順序 (ascending, descending)
    
    Returns:
        取得した論文のリスト
    """
    # ソートオプションの検証
    if sort_by not in SORT_OPTIONS:
        print(f"Warning: Invalid sort_by option '{sort_by}'. Using 'submittedDate' instead.")
        sort_by = "submittedDate"
        
    if sort_order not in SORT_DIRECTIONS:
        print(f"Warning: Invalid sort_order option '{sort_order}'. Using 'descending' instead.")
        sort_order = "descending"
    
    # 文字列形式の日付をdatetimeオブジェクトに変換
    start_date = datetime.strptime(date_from_str, "%Y-%m-%d")
    end_date = datetime.strptime(date_to_str, "%Y-%m-%d")
    
    print(f"\nSearch parameters:\n  - Query: {query}")
    if category:
        print(f"  - Category: {category} ({ARXIV_CATEGORIES.get(category, 'Unknown')})")
    print(f"  - Date range: {date_from_str} to {date_to_str}")
    print(f"  - Sort by: {sort_by} ({sort_order})\n")
    
    all_papers = []
    batch_size = 100  # 各ページのサイズ (arXiv APIの推奨値)
    start = 0
    total_fetched = 0
    
    while True:
        print(f"Fetching papers batch: start={start}, batch_size={batch_size}")
        
        try:
            # 論文を取得
            papers = api_client.search(
                query=query,
                category=category,
                start_date=start_date,
                end_date=end_date,
                max_results=batch_size,
                start=start,  # ページネーション用パラメータ
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # 結果がない場合は終了
            if not papers:
                print("No more papers found.")
                break
                
            batch_count = len(papers)
            all_papers.extend(papers)
            total_fetched += batch_count
            
            print(f"Retrieved {batch_count} papers (Total: {total_fetched})")
            
            # 取得した論文数がバッチサイズより少ない場合は終了
            if batch_count < batch_size:
                print("Reached the end of results.")
                break
                
            # 次のページに移動
            start += batch_size
            
            # API制限を避けるための適切な間隔
            print("Waiting 3 seconds before next request...")
            time.sleep(3)
            
        except Exception as e:
            print(f"Error fetching papers: {e}")
            # エラー発生時は少し待って再試行
            print("Waiting 10 seconds before retrying...")
            time.sleep(10)
            continue
    
    return all_papers


def parse_arguments():
    """
    コマンドライン引数を解析する
    
    Returns:
        解析された引数
    """
    parser = argparse.ArgumentParser(description="arXiv paper search and download tool")
    
    # 基本的な検索パラメータ
    parser.add_argument('query', type=str, nargs='?', default="prompt engineering", 
                      help="Search query (default: 'prompt engineering')")
    
    # カテゴリフィルタリング
    parser.add_argument('--category', '-c', type=str, choices=list(ARXIV_CATEGORIES.keys()), 
                      help="Filter by arXiv category (e.g. 'cs.AI', 'cs.CL')")
    
    # 期間指定オプション群
    time_group = parser.add_mutually_exclusive_group()
    
    # 形式1: 単位付きの相対期間 (3d, 2w, 6m, 1y)
    time_group.add_argument('--period', '-P', type=str, 
                      help="Time period in relative format (e.g. '3d' for 3 days, '2w' for 2 weeks, "
                           "'6m' for 6 months, '1y' for 1 year)")
    
    # 形式2: 日付範囲 (YYYY-MM-DD~YYYY-MM-DD)
    time_group.add_argument('--date-range', '-dr', type=str, 
                      help="Date range in format 'YYYY-MM-DD~YYYY-MM-DD'")
    
    # 形式3: 後方互換性のための形式 (from/to)
    time_group.add_argument('--from-date', '-f', type=str, 
                     help="Start date in YYYY-MM-DD format")
    
    time_group.add_argument('--to-date', '-t', type=str, 
                     help="End date in YYYY-MM-DD format (default: today)")
    
    # よく使われる期間のプリセット
    preset_group = parser.add_mutually_exclusive_group()
    preset_group.add_argument('--last-month', action='store_true', 
                      help="Last month (shortcut for --period 1m)")
    
    preset_group.add_argument('--last-3-months', action='store_true', 
                      help="Last 3 months (shortcut for --period 3m)")
    
    preset_group.add_argument('--last-6-months', action='store_true', 
                      help="Last 6 months (shortcut for --period 6m)")
    
    preset_group.add_argument('--last-year', action='store_true', 
                      help="Last year (shortcut for --period 1y)")
    
    preset_group.add_argument('--last-week', action='store_true', 
                      help="Last week (shortcut for --period 1w)")
    
    # ソートオプション
    parser.add_argument('--sort-by', '-s', type=str, choices=SORT_OPTIONS, 
                      default="submittedDate", 
                      help="Sort results by (default: submittedDate)")
    
    parser.add_argument('--sort-order', '-o', type=str, choices=SORT_DIRECTIONS, 
                      default="descending", 
                      help="Sort direction (default: descending)")
    
    # PDF関連オプション
    parser.add_argument('--download-pdf', '-d', action='store_true', 
                      help="Download PDFs for all papers found")
    
    parser.add_argument('--max-downloads', '-m', type=int, default=10, 
                      help="Maximum number of PDFs to download (default: 10, use 0 for all)")
    
    parser.add_argument('--parallel', '-p', type=int, default=3, 
                      help="Number of parallel downloads (default: 3)")
    
    # データベース関連オプション
    parser.add_argument('--skip-db', action='store_true', 
                      help="Skip storing papers in the database")
    
    parser.add_argument('--list-categories', '-l', action='store_true', 
                      help="List available arXiv categories and exit")
    
    return parser.parse_args()


def list_categories():
    """利用可能なarXivカテゴリを表示する"""
    print("Available arXiv categories:\n")
    for cat_id, cat_name in sorted(ARXIV_CATEGORIES.items()):
        print(f"  {cat_id}: {cat_name}")


def main():
    # コマンドライン引数を解析
    args = parse_arguments()
    
    # カテゴリ一覧表示モード
    if args.list_categories:
        list_categories()
        return
    
    # クライアントとデータベースの初期化
    print("Initializing clients...")
    api_client = ArxivApiClient()
    
    if not args.skip_db:
        db_manager = DatabaseManager(db_path=DB_PATH)
        # データベースの初期化
        db_manager.initialize_database()
    
    # 期間指定を処理する
    period_str = None
    
    # プリセットオプションの処理
    if args.last_week:
        period_str = "1w"
    elif args.last_month:
        period_str = "1m"
    elif args.last_3_months:
        period_str = "3m"
    elif args.last_6_months:
        period_str = "6m"
    elif args.last_year:
        period_str = "1y"
    # 直接期間指定
    elif args.period:
        period_str = args.period
    # 日付範囲指定
    elif args.date_range:
        period_str = args.date_range
    # 後方互換性のための形式 (from/to)
    elif args.from_date and args.to_date:
        period_str = f"{args.from_date}~{args.to_date}"
    elif args.from_date:
        period_str = args.from_date
    elif args.to_date:
        # 開始日をデフォルト値 (2023-01-01) として設定
        period_str = f"2023-01-01~{args.to_date}"
    else:
        # デフォルトは2023年以降
        period_str = "2023-01-01"
    
    # 期間文字列を解析する
    start_date, end_date = parse_time_period(period_str)
    date_from_str = format_date(start_date)
    date_to_str = format_date(end_date)
    
    # 全ての論文を取得
    all_papers = fetch_all_papers(
        api_client, 
        args.query, 
        date_from_str, 
        date_to_str, 
        category=args.category,
        sort_by=args.sort_by,
        sort_order=args.sort_order
    )
    
    total_papers = len(all_papers)
    print(f"Found a total of {total_papers} papers matching the criteria")
    
    # データがない場合は終了
    if not all_papers:
        print("No papers found matching the criteria.")
        return
    
    # データベースへの保存
    if not args.skip_db:
        print("\nStoring papers in database...")
        try:
            # store_papersメソッドは値を返さないが、エラーがスローされなければ成功
            db_manager.store_papers(all_papers)
            print(f"Successfully stored {total_papers} papers in the database at {DB_PATH}")
        except Exception as e:
            print(f"Error storing papers: {str(e)}")
    
    # PDFダウンロード
    if args.download_pdf:
        # ダウンロード数の制限処理
        max_downloads = args.max_downloads if args.max_downloads > 0 else total_papers
        papers_to_download = all_papers[:max_downloads]
        
        print(f"\nDownloading PDFs ({len(papers_to_download)} of {total_papers} papers)...")
        downloaded_files = download_pdfs(papers_to_download, PDF_DIR, max_workers=args.parallel)
        
        print(f"\nDownloaded {len(downloaded_files)} PDFs to {PDF_DIR}")
        if len(downloaded_files) < len(papers_to_download):
            print(f"  Warning: {len(papers_to_download) - len(downloaded_files)} downloads failed")
    
    # 最新の5件を表示
    print("\nLatest 5 papers:\n")
    for i, paper in enumerate(all_papers[:5]):
        print(f"{i+1}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   Published: {paper['published_date']}")
        print(f"   URL: {paper['id']}")
        if args.download_pdf:
            arxiv_id = paper['id'].split('/')[-1]
            pdf_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
            if os.path.exists(pdf_path):
                print(f"   PDF: {pdf_path}")
        print()


if __name__ == "__main__":
    main()
