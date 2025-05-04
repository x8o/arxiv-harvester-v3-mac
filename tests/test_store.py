"""Tests for the Store module."""

import pytest
import os
import sqlite3
import json
from datetime import datetime

# Import the module we'll be testing
from src.arxiv_harvester.store.database import DatabaseManager


class TestDatabaseManager:
    """Test suite for the DatabaseManager class."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Fixture to create a temporary database path."""
        return str(tmp_path / "test_arxiv.db")
    
    @pytest.fixture
    def db_manager(self, db_path):
        """Fixture to create a DatabaseManager instance."""
        manager = DatabaseManager(db_path)
        # Setup: ensure tables are created
        manager.initialize_database()
        return manager
    
    @pytest.fixture
    def sample_papers(self):
        """Fixture to provide sample paper data."""
        return [
            {
                'id': 'http://arxiv.org/abs/2104.12345',
                'title': 'Sample Paper Title 1',
                'summary': 'This is a sample abstract for paper 1.',
                'authors': ['Author One', 'Author Two'],
                'published_date': '2021-04-15T00:00:00Z',
                'pdf_url': 'http://arxiv.org/pdf/2104.12345'
            },
            {
                'id': 'http://arxiv.org/abs/2104.67890',
                'title': 'Sample Paper Title 2',
                'summary': 'This is a sample abstract for paper 2.',
                'authors': ['Author Three'],
                'published_date': '2021-04-16T00:00:00Z',
                'pdf_url': 'http://arxiv.org/pdf/2104.67890'
            }
        ]
    
    # Test 1: Verify database initialization
    def test_initialize_database(self, db_manager, db_path):
        """Test that the database is properly initialized with the expected tables."""
        # Check if the database file was created
        assert os.path.exists(db_path)
        
        # Connect directly to the database to inspect its structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the papers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
        assert cursor.fetchone() is not None
        
        # Check if the authors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='authors'")
        assert cursor.fetchone() is not None
        
        # Check if the paper_authors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_authors'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    # Test 2: Test storing papers in the database
    def test_store_papers(self, db_manager, sample_papers):
        """Test storing papers in the database."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Retrieve all papers to verify they were stored
        stored_papers = db_manager.get_all_papers()
        
        # Check that the number of stored papers matches the sample
        assert len(stored_papers) == len(sample_papers)
        
        # Check the content of the first paper
        assert stored_papers[0]['title'] == sample_papers[0]['title']
        assert stored_papers[0]['summary'] == sample_papers[0]['summary']
    
    # Test 3: Test retrieving papers by ID
    def test_get_paper_by_id(self, db_manager, sample_papers):
        """Test retrieving a specific paper by its ID."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Extract the arxiv ID from the full ID URL
        paper_id = sample_papers[0]['id'].split('/')[-1]
        
        # Retrieve the paper by ID
        paper = db_manager.get_paper_by_id(paper_id)
        
        # Verify the retrieved paper matches the sample
        assert paper is not None
        assert paper['title'] == sample_papers[0]['title']
    
    # Test 4: Test updating existing papers
    def test_update_existing_paper(self, db_manager, sample_papers):
        """Test updating an existing paper in the database."""
        # Store the initial paper
        db_manager.store_papers([sample_papers[0]])
        
        # Create an updated version of the paper
        updated_paper = sample_papers[0].copy()
        updated_paper['title'] = 'Updated Title'
        updated_paper['summary'] = 'Updated abstract'
        
        # Store the updated paper (should update the existing record)
        db_manager.store_papers([updated_paper])
        
        # Retrieve the paper to verify it was updated
        stored_papers = db_manager.get_all_papers()
        
        # Should still have only one paper
        assert len(stored_papers) == 1
        
        # Verify the paper was updated
        assert stored_papers[0]['title'] == 'Updated Title'
        assert stored_papers[0]['summary'] == 'Updated abstract'
    
    # Test 5: Test retrieving papers by date range
    def test_get_papers_by_date_range(self, db_manager, sample_papers):
        """Test retrieving papers published within a specific date range."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Define date range (should include both papers)
        start_date = datetime(2021, 4, 14)
        end_date = datetime(2021, 4, 17)
        
        # Retrieve papers within the date range
        papers = db_manager.get_papers_by_date_range(start_date, end_date)
        
        # Verify both papers are returned
        assert len(papers) == 2
        
        # Define a narrower date range (should include only the second paper)
        start_date = datetime(2021, 4, 16)
        end_date = datetime(2021, 4, 17)
        
        # Retrieve papers within the narrower date range
        papers = db_manager.get_papers_by_date_range(start_date, end_date)
        
        # Verify only one paper is returned
        assert len(papers) == 1
        assert papers[0]['title'] == sample_papers[1]['title']
    
    # Test 6: Test retrieving papers by author
    def test_get_papers_by_author(self, db_manager, sample_papers):
        """Test retrieving papers by a specific author."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Retrieve papers by the first author (should return the first paper)
        papers = db_manager.get_papers_by_author('Author One')
        
        # Verify the correct paper is returned
        assert len(papers) == 1
        assert papers[0]['title'] == sample_papers[0]['title']
        
        # Retrieve papers by the third author (should return the second paper)
        papers = db_manager.get_papers_by_author('Author Three')
        
        # Verify the correct paper is returned
        assert len(papers) == 1
        assert papers[0]['title'] == sample_papers[1]['title']
    
    # Test 7: Test searching papers by keyword in title
    def test_search_papers_by_title(self, db_manager, sample_papers):
        """Test searching papers by keywords in the title."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Search for papers with 'Sample' in the title (should return both)
        papers = db_manager.search_papers(title_keyword='Sample')
        
        # Verify both papers are returned
        assert len(papers) == 2
        
        # Search for papers with 'Title 1' in the title (should return only the first)
        papers = db_manager.search_papers(title_keyword='Title 1')
        
        # Verify only the first paper is returned
        assert len(papers) == 1
        assert papers[0]['title'] == sample_papers[0]['title']
    
    # Test 8: Test searching papers by keyword in abstract
    def test_search_papers_by_abstract(self, db_manager, sample_papers):
        """Test searching papers by keywords in the abstract."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Search for papers with 'abstract' in the summary (should return both)
        papers = db_manager.search_papers(abstract_keyword='abstract')
        
        # Verify both papers are returned
        assert len(papers) == 2
        
        # Search for papers with 'paper 2' in the summary (should return only the second)
        papers = db_manager.search_papers(abstract_keyword='paper 2')
        
        # Verify only the second paper is returned
        assert len(papers) == 1
        assert papers[0]['title'] == sample_papers[1]['title']
    
    # Test 9: Test deleting a paper
    def test_delete_paper(self, db_manager, sample_papers):
        """Test deleting a paper from the database."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Extract the arxiv ID from the full ID URL
        paper_id = sample_papers[0]['id'].split('/')[-1]
        
        # Delete the first paper
        db_manager.delete_paper(paper_id)
        
        # Retrieve all papers
        remaining_papers = db_manager.get_all_papers()
        
        # Verify only one paper remains
        assert len(remaining_papers) == 1
        assert remaining_papers[0]['title'] == sample_papers[1]['title']
    
    # Test 10: Test retrieving the most recent papers
    def test_get_recent_papers(self, db_manager, sample_papers):
        """Test retrieving the most recently published papers."""
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Retrieve the most recent paper (limit=1)
        recent_papers = db_manager.get_recent_papers(limit=1)
        
        # Verify that only the most recent paper is returned
        assert len(recent_papers) == 1
        assert recent_papers[0]['title'] == sample_papers[1]['title']  # The second paper is more recent
    
    # Test 11: Test handling of malformed paper data
    def test_handle_malformed_paper_data(self, db_manager):
        """Test proper handling of malformed paper data."""
        # Create paper with missing required fields
        malformed_paper = {
            'id': 'http://arxiv.org/abs/2104.12345',
            # Missing title and other fields
        }
        
        # Attempt to store the malformed paper
        with pytest.raises(ValueError) as excinfo:
            db_manager.store_papers([malformed_paper])
        
        assert "Missing required fields" in str(excinfo.value)
    
    # Test 12: Test counting papers by category
    def test_count_papers_by_category(self, db_manager, sample_papers):
        """Test counting papers by category."""
        # Add category field to sample papers
        sample_papers[0]['category'] = 'cs.AI'
        sample_papers[1]['category'] = 'cs.CL'
        
        # Store the sample papers
        db_manager.store_papers(sample_papers)
        
        # Get counts by category
        category_counts = db_manager.count_papers_by_category()
        
        # Verify the counts
        assert len(category_counts) == 2
        assert category_counts['cs.AI'] == 1
        assert category_counts['cs.CL'] == 1
    
    # Test 13: Test retrieving papers with pagination
    def test_get_papers_with_pagination(self, db_manager, sample_papers):
        """Test retrieving papers with pagination."""
        # Create and store more sample papers to test pagination
        additional_papers = []
        for i in range(10):
            paper = {
                'id': f'http://arxiv.org/abs/{2104+i}',
                'title': f'Additional Paper {i}',
                'summary': f'This is abstract {i}',
                'authors': [f'Author {i}'],
                'published_date': f'2021-05-{i+1:02d}T00:00:00Z',
                'pdf_url': f'http://arxiv.org/pdf/{2104+i}'
            }
            additional_papers.append(paper)
        
        # Store all papers
        db_manager.store_papers(sample_papers + additional_papers)
        
        # Test first page (limit=5, offset=0)
        page1 = db_manager.get_papers(limit=5, offset=0)
        assert len(page1) == 5
        
        # Test second page (limit=5, offset=5)
        page2 = db_manager.get_papers(limit=5, offset=5)
        assert len(page2) == 5
        
        # Verify that the pages contain different papers
        page1_ids = [p['id'] for p in page1]
        page2_ids = [p['id'] for p in page2]
        assert not set(page1_ids).intersection(set(page2_ids))  # No overlap between pages
    
    # Test 14: Test database backup functionality
    def test_backup_database(self, db_manager, sample_papers, tmp_path):
        """Test backing up the database."""
        # Store sample papers
        db_manager.store_papers(sample_papers)
        
        # Create backup path
        backup_path = str(tmp_path / "backup.db")
        
        # Perform backup
        db_manager.backup_database(backup_path)
        
        # Verify backup file exists
        assert os.path.exists(backup_path)
        
        # Connect to backup and verify data integrity
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Verify backup contains the same number of papers
        assert count == len(sample_papers)
    
    # Test 15: Test transaction handling (rollback on error)
    def test_transaction_rollback(self, db_manager, sample_papers, monkeypatch):
        """Test that transactions are properly rolled back on error."""
        # Store the first paper successfully
        db_manager.store_papers([sample_papers[0]])
        
        # Modify the _insert_author method to raise an exception after inserting the paper
        original_insert_author = db_manager._insert_author
        def mock_insert_author(conn, author_name):
            if author_name == "Author Three":  # Only fail on the second paper's author
                raise Exception("Simulated database error")
            return original_insert_author(conn, author_name)
        
        monkeypatch.setattr(db_manager, "_insert_author", mock_insert_author)
        
        # Try to store the second paper, which should fail
        with pytest.raises(Exception):
            db_manager.store_papers([sample_papers[1]])
        
        # Verify only the first paper is in the database
        stored_papers = db_manager.get_all_papers()
        assert len(stored_papers) == 1
        assert stored_papers[0]['title'] == sample_papers[0]['title']
