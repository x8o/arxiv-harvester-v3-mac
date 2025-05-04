"""Database management for arXiv Harvester.

Provides functionality for storing and retrieving arXiv papers in a SQLite database.
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple


class DatabaseManager:
    """Manager for the arXiv papers database.

    Handles database operations for storing and retrieving arXiv papers,
    including relationships with authors and categories.
    """

    def __init__(self, db_path: str):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    def initialize_database(self):
        """Create the database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create papers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            arxiv_id TEXT UNIQUE,
            title TEXT NOT NULL,
            summary TEXT,
            published_date TEXT,
            pdf_url TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create authors table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)

        # Create paper_authors relationship table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_authors (
            paper_id TEXT,
            author_id INTEGER,
            PRIMARY KEY (paper_id, author_id),
            FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors (id) ON DELETE CASCADE
        )
        """)

        conn.commit()
        conn.close()

    def store_papers(self, papers: List[Dict[str, Any]]):
        """Store a list of arXiv papers in the database.

        Args:
            papers: List of paper dictionaries with fields: id, title, summary,
                   authors, published_date, pdf_url, and optionally category

        Raises:
            ValueError: If the paper data is missing required fields
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Begin transaction - we want to ensure all paper data is stored atomically
            conn.execute("BEGIN TRANSACTION")

            for paper in papers:
                # Validate paper data
                if 'id' not in paper or 'title' not in paper:
                    raise ValueError(f"Missing required fields in paper data: {paper}")

                # Extract arXiv ID from the full URL
                full_id = paper['id']
                arxiv_id = full_id.split('/')[-1] if '/' in full_id else full_id

                # Insert or update paper record
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO papers
                (id, arxiv_id, title, summary, published_date, pdf_url, category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    full_id,
                    arxiv_id,
                    paper['title'],
                    paper.get('summary', ''),
                    paper.get('published_date', ''),
                    paper.get('pdf_url', ''),
                    paper.get('category', None)
                ))

                # Handle authors
                if 'authors' in paper and paper['authors']:
                    # Remove existing author relationships
                    cursor.execute("DELETE FROM paper_authors WHERE paper_id = ?", (full_id,))

                    # Add authors and relationships
                    for author_name in paper['authors']:
                        author_id = self._insert_author(conn, author_name)
                        cursor.execute("""
                        INSERT OR IGNORE INTO paper_authors (paper_id, author_id)
                        VALUES (?, ?)
                        """, (full_id, author_id))

            # Commit the transaction
            conn.commit()

        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _insert_author(self, conn, author_name: str) -> int:
        """Insert an author if they don't exist and return their ID."""
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO authors (name) VALUES (?)
        """, (author_name,))

        cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
        return cursor.fetchone()[0]

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Retrieve all papers from the database.

        Returns:
            List of paper dictionaries
        """
        return self.get_papers()

    def get_papers(self, limit: int = None, offset: int = 0, order_by: str = "published_date", order_direction: str = "ASC") -> List[Dict[str, Any]]:
        """Retrieve papers with pagination support.

        Args:
            limit: Maximum number of papers to return (None for all)
            offset: Number of papers to skip
            order_by: Field to order by (default: published_date)
            order_direction: Direction to order (ASC or DESC)

        Returns:
            List of paper dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with pagination
        query = f"SELECT * FROM papers ORDER BY {order_by} {order_direction}"
        params = []

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset > 0:
            query += " OFFSET ?"
            params.append(offset)

        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]

        # Add authors to each paper
        for paper in papers:
            paper['authors'] = self._get_paper_authors(conn, paper['id'])

        conn.close()
        return papers

    def _get_paper_authors(self, conn, paper_id: str) -> List[str]:
        """Get the list of authors for a paper."""
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.name FROM authors a
        JOIN paper_authors pa ON pa.author_id = a.id
        WHERE pa.paper_id = ?
        ORDER BY a.name
        """, (paper_id,))

        return [row[0] for row in cursor.fetchall()]

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a paper by its arXiv ID.

        Args:
            paper_id: arXiv ID (e.g., '2104.12345')

        Returns:
            Paper dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # First try with the ID as is
        cursor.execute("SELECT * FROM papers WHERE arxiv_id = ?", (paper_id,))
        row = cursor.fetchone()

        # If not found, try with the full URL format
        if row is None:
            cursor.execute("SELECT * FROM papers WHERE id = ?",
                         (f"http://arxiv.org/abs/{paper_id}",))
            row = cursor.fetchone()

        if row is None:
            conn.close()
            return None

        paper = dict(row)
        paper['authors'] = self._get_paper_authors(conn, paper['id'])

        conn.close()
        return paper

    def get_papers_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Retrieve papers published within a date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of paper dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Format dates to ISO format
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")

        cursor.execute("""
        SELECT * FROM papers
        WHERE published_date >= ? AND published_date <= ?
        ORDER BY published_date DESC
        """, (start_str, end_str))

        papers = [dict(row) for row in cursor.fetchall()]

        # Add authors to each paper
        for paper in papers:
            paper['authors'] = self._get_paper_authors(conn, paper['id'])

        conn.close()
        return papers

    def get_papers_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        """Retrieve papers by a specific author.

        Args:
            author_name: Author name to search for

        Returns:
            List of paper dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT p.* FROM papers p
        JOIN paper_authors pa ON pa.paper_id = p.id
        JOIN authors a ON a.id = pa.author_id
        WHERE a.name = ?
        ORDER BY p.published_date DESC
        """, (author_name,))

        papers = [dict(row) for row in cursor.fetchall()]

        # Add authors to each paper
        for paper in papers:
            paper['authors'] = self._get_paper_authors(conn, paper['id'])

        conn.close()
        return papers

    def search_papers(self, title_keyword: str = None, abstract_keyword: str = None) -> List[Dict[str, Any]]:
        """Search papers by keywords in title or abstract.

        Args:
            title_keyword: Keyword to search in titles
            abstract_keyword: Keyword to search in abstracts

        Returns:
            List of matching paper dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        if title_keyword:
            query += " AND title LIKE ?"
            params.append(f'%{title_keyword}%')

        if abstract_keyword:
            query += " AND summary LIKE ?"
            params.append(f'%{abstract_keyword}%')

        query += " ORDER BY published_date DESC"

        cursor.execute(query, params)
        papers = [dict(row) for row in cursor.fetchall()]

        # Add authors to each paper
        for paper in papers:
            paper['authors'] = self._get_paper_authors(conn, paper['id'])

        conn.close()
        return papers

    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper from the database.

        Args:
            paper_id: arXiv ID of the paper to delete

        Returns:
            True if the paper was deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")

            # First, determine the full ID if we have only the arXiv ID
            cursor.execute("SELECT id FROM papers WHERE arxiv_id = ?", (paper_id,))
            row = cursor.fetchone()

            full_id = None
            if row:
                full_id = row[0]
            else:
                # Try with the full URL format
                full_id = f"http://arxiv.org/abs/{paper_id}"
                cursor.execute("SELECT id FROM papers WHERE id = ?", (full_id,))
                if not cursor.fetchone():
                    conn.rollback()
                    conn.close()
                    return False

            # Delete from paper_authors (cascade should handle this, but being explicit)
            cursor.execute("DELETE FROM paper_authors WHERE paper_id = ?", (full_id,))

            # Delete the paper
            cursor.execute("DELETE FROM papers WHERE id = ?", (full_id,))

            # Remove orphaned authors
            cursor.execute("""
            DELETE FROM authors
            WHERE id NOT IN (SELECT DISTINCT author_id FROM paper_authors)
            """)

            # Commit transaction
            conn.commit()
            result = cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return result

    def get_recent_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently published papers.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of paper dictionaries, ordered by publication date
        """
        return self.get_papers(limit=limit, order_direction="DESC")

    def count_papers_by_category(self) -> Dict[str, int]:
        """Count papers by category.

        Returns:
            Dictionary mapping category names to paper counts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM papers
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
        """)

        counts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        return counts

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database file.

        Args:
            backup_path: Path to save the backup file

        Returns:
            True if backup was successful, False otherwise
        """
        try:
            # Ensure the source database exists
            if not os.path.exists(self.db_path):
                return False

            # Make sure the backup directory exists
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            return True

        except Exception:
            return False
