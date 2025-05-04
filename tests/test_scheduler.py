"""Tests for the Scheduler module."""

import pytest
from unittest.mock import patch
import os
import tempfile
from datetime import datetime, timedelta

# Import the module we'll be testing
from src.arxiv_harvester.scheduler.scheduler import Scheduler
from src.arxiv_harvester.api.client import ArxivApiClient
from src.arxiv_harvester.store.database import DatabaseManager
from src.arxiv_harvester.notify.slack import SlackNotifier


class TestScheduler:
    """Test suite for the Scheduler class."""

    @pytest.fixture
    def temp_db_path(self):
        """Fixture to create a temporary database path."""
        _, temp_path = tempfile.mkstemp(suffix=".db")
        yield temp_path
        # Cleanup after test
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def scheduler(self, temp_db_path):
        """Fixture to create a Scheduler instance."""
        api_client = ArxivApiClient()
        db_manager = DatabaseManager(temp_db_path)
        db_manager.initialize_database()
        notifier = SlackNotifier()

        scheduler = Scheduler(
            api_client=api_client,
            db_manager=db_manager,
            notifier=notifier
        )
        return scheduler

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
                'pdf_url': 'http://arxiv.org/pdf/2104.12345',
                'category': 'cs.AI'
            },
            {
                'id': 'http://arxiv.org/abs/2104.67890',
                'title': 'Sample Paper Title 2',
                'summary': 'This is a sample abstract for paper 2.',
                'authors': ['Author Three'],
                'published_date': '2021-04-16T00:00:00Z',
                'pdf_url': 'http://arxiv.org/pdf/2104.67890',
                'category': 'cs.CL'
            }
        ]

    # Test 1: Test initialization
    def test_init(self, scheduler):
        """Test the initialization of the Scheduler."""
        assert hasattr(scheduler, 'api_client')
        assert hasattr(scheduler, 'db_manager')
        assert hasattr(scheduler, 'notifier')
        assert scheduler.query == ''
        assert scheduler.categories == []
        assert scheduler.max_results == 50

    # Test 2: Test setting search parameters
    def test_set_search_parameters(self, scheduler):
        """Test setting search parameters."""
        scheduler.set_search_parameters(
            query="machine learning",
            categories=["cs.AI", "cs.CL"],
            max_results=100
        )

        assert scheduler.query == "machine learning"
        assert scheduler.categories == ["cs.AI", "cs.CL"]
        assert scheduler.max_results == 100

    # Test 3: Test fetching papers
    @patch.object(ArxivApiClient, 'search')
    def test_fetch_papers(self, mock_search, scheduler, sample_papers):
        """Test fetching papers from the API."""
        # Set up the mock
        mock_search.return_value = sample_papers

        # Set search parameters
        scheduler.set_search_parameters(
            query="machine learning",
            categories=["cs.AI"]
        )

        # Call the method
        papers = scheduler.fetch_papers()

        # Verify the result
        assert papers == sample_papers
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        assert kwargs['query'] == "machine learning"
        assert kwargs['category'] == "cs.AI"

    # Test 4: Test fetching papers with multiple categories
    @patch.object(ArxivApiClient, 'search')
    def test_fetch_papers_multiple_categories(self, mock_search, scheduler, sample_papers):
        """Test fetching papers from multiple categories."""
        # Set up the mock to return different papers for each category
        mock_search.side_effect = [
            [sample_papers[0]],  # For cs.AI
            [sample_papers[1]]   # For cs.CL
        ]

        # Set search parameters with multiple categories
        scheduler.set_search_parameters(
            query="neural networks",
            categories=["cs.AI", "cs.CL"]
        )

        # Call the method
        papers = scheduler.fetch_papers()

        # Verify the result
        assert len(papers) == 2
        assert papers[0] == sample_papers[0]
        assert papers[1] == sample_papers[1]
        assert mock_search.call_count == 2

    # Test 5: Test storing fetched papers
    @patch.object(DatabaseManager, 'store_papers')
    def test_store_papers(self, mock_store, scheduler, sample_papers):
        """Test storing papers in the database."""
        # Call the method
        scheduler.store_papers(sample_papers)

        # Verify the call
        mock_store.assert_called_once_with(sample_papers)

    # Test 6: Test checking for new papers
    @patch.object(DatabaseManager, 'get_paper_by_id')
    def test_filter_new_papers(self, mock_get_paper, scheduler, sample_papers):
        """Test filtering for new papers not already in the database."""
        # Set up the mock to simulate one existing and one new paper
        mock_get_paper.side_effect = [
            None,  # First paper not found (new)
            sample_papers[1]  # Second paper found (existing)
        ]

        # Call the method
        new_papers = scheduler.filter_new_papers(sample_papers)

        # Verify the result
        assert len(new_papers) == 1
        assert new_papers[0] == sample_papers[0]
        assert mock_get_paper.call_count == 2

    # Test 7: Test sending notifications
    @patch.object(SlackNotifier, 'post_papers_to_slack')
    def test_send_notifications(self, mock_post, scheduler, sample_papers):
        """Test sending notifications for new papers."""
        # Mock successful posting
        mock_post.return_value = True

        # Set webhook URL
        webhook_url = "https://hooks.slack.com/services/fake/webhook"
        scheduler.set_slack_webhook(webhook_url)

        # Call the method
        result = scheduler.send_notifications(sample_papers)

        # Verify the result
        assert result is True
        mock_post.assert_called_once_with(
            sample_papers,
            webhook_url,
            use_blocks=True,
            pre_message="New arXiv papers matching your criteria:"
        )

    # Test 8: Test running the full harvest process
    @patch.object(Scheduler, 'fetch_papers')
    @patch.object(Scheduler, 'filter_new_papers')
    @patch.object(Scheduler, 'store_papers')
    @patch.object(Scheduler, 'send_notifications')
    def test_run_harvest(self, mock_send, mock_store, mock_filter, mock_fetch, scheduler, sample_papers):
        """Test running the full harvest process."""
        # Set up the mocks
        mock_fetch.return_value = sample_papers
        mock_filter.return_value = [sample_papers[0]]  # Only one new paper
        mock_store.return_value = None
        mock_send.return_value = True

        # Set search parameters and webhook
        scheduler.set_search_parameters(query="deep learning")
        scheduler.set_slack_webhook("https://hooks.slack.com/services/fake/webhook")

        # Call the method
        result = scheduler.run_harvest()

        # Verify the process flow and result
        assert result is True
        mock_fetch.assert_called_once()
        mock_filter.assert_called_once_with(sample_papers)
        mock_store.assert_called_once_with([sample_papers[0]])
        mock_send.assert_called_once_with([sample_papers[0]])

    # Test 9: Test handling no new papers
    @patch.object(Scheduler, 'fetch_papers')
    @patch.object(Scheduler, 'filter_new_papers')
    @patch.object(Scheduler, 'store_papers')
    @patch.object(Scheduler, 'send_notifications')
    def test_run_harvest_no_new_papers(self, mock_send, mock_store, mock_filter, mock_fetch, scheduler, sample_papers):
        """Test running the harvest when there are no new papers."""
        # Set up the mocks
        mock_fetch.return_value = sample_papers
        mock_filter.return_value = []  # No new papers

        # Call the method
        result = scheduler.run_harvest()

        # Verify the process flow and result
        assert result is True
        mock_fetch.assert_called_once()
        mock_filter.assert_called_once_with(sample_papers)
        mock_store.assert_not_called()
        mock_send.assert_not_called()

    # Test 10: Test handling fetch errors
    @patch.object(ArxivApiClient, 'search')
    def test_handle_fetch_error(self, mock_search, scheduler):
        """Test handling errors during paper fetching."""
        # Set up the mock to raise an exception
        mock_search.side_effect = Exception("API Error")

        # Set search parameters
        scheduler.set_search_parameters(query="error test")

        # Call the method and verify it catches the exception
        with pytest.raises(Exception) as excinfo:
            scheduler.fetch_papers()

        assert "Error fetching papers" in str(excinfo.value)

    # Test 11: Test saving and loading state
    def test_save_load_state(self, scheduler, temp_db_path):
        """Test saving and loading the scheduler state."""
        # Set up the state
        scheduler.set_search_parameters(
            query="deep learning",
            categories=["cs.AI", "cs.CL"],
            max_results=75
        )
        scheduler.set_slack_webhook("https://hooks.slack.com/services/test/webhook")
        scheduler.set_last_run_time(datetime.now())

        # Create a state file path
        state_file = os.path.join(os.path.dirname(temp_db_path), "scheduler_state.json")

        # Save the state
        scheduler.save_state(state_file)

        # Create a new scheduler
        new_scheduler = Scheduler(
            api_client=ArxivApiClient(),
            db_manager=DatabaseManager(temp_db_path),
            notifier=SlackNotifier()
        )

        # Load the state
        new_scheduler.load_state(state_file)

        # Verify the state was loaded correctly
        assert new_scheduler.query == "deep learning"
        assert new_scheduler.categories == ["cs.AI", "cs.CL"]
        assert new_scheduler.max_results == 75
        assert new_scheduler.slack_webhook == "https://hooks.slack.com/services/test/webhook"
        assert new_scheduler.last_run_time is not None

        # Clean up
        if os.path.exists(state_file):
            os.remove(state_file)

    # Test 12: Test handling notification failure
    @patch.object(SlackNotifier, 'post_papers_to_slack')
    def test_handle_notification_failure(self, mock_post, scheduler, sample_papers):
        """Test handling notification failures."""
        # Mock failed posting
        mock_post.return_value = False

        # Set webhook URL
        webhook_url = "https://hooks.slack.com/services/fake/webhook"
        scheduler.set_slack_webhook(webhook_url)

        # Call the method
        result = scheduler.send_notifications(sample_papers)

        # Verify the result
        assert result is False

    # Test 13: Test checking if it's time to run
    def test_is_time_to_run(self, scheduler):
        """Test checking if it's time to run based on schedule."""
        # Set up a weekly schedule
        scheduler.set_schedule("weekly")

        # Set last run time to 8 days ago (should run)
        past_time = datetime.now() - timedelta(days=8)
        scheduler.set_last_run_time(past_time)
        assert scheduler.is_time_to_run() is True

        # Set last run time to 2 days ago (should not run)
        recent_time = datetime.now() - timedelta(days=2)
        scheduler.set_last_run_time(recent_time)
        assert scheduler.is_time_to_run() is False

        # Set schedule to daily
        scheduler.set_schedule("daily")
        assert scheduler.is_time_to_run() is True

    # Test 14: Test command-line argument parsing
    def test_parse_arguments(self, scheduler):
        """Test parsing command-line arguments."""
        # Test with arguments
        args = [
            "--query", "neural networks",
            "--categories", "cs.AI,cs.CL",
            "--max-results", "25",
            "--webhook", "https://example.com/webhook",
            "--force-run"
        ]

        # Parse arguments
        parsed = scheduler.parse_arguments(args)

        # Verify parsing results
        assert parsed.query == "neural networks"
        assert parsed.categories == "cs.AI,cs.CL"
        assert parsed.max_results == 25
        assert parsed.webhook == "https://example.com/webhook"
        assert parsed.force_run is True

    # Test 15: Test full workflow with file state
    @patch.object(Scheduler, 'fetch_papers')
    @patch.object(Scheduler, 'filter_new_papers')
    @patch.object(Scheduler, 'store_papers')
    @patch.object(Scheduler, 'send_notifications')
    @patch.object(Scheduler, 'save_state')
    def test_workflow_with_state(self, mock_save, mock_send, mock_store, mock_filter, mock_fetch,
                                 scheduler, sample_papers, temp_db_path):
        """Test the full workflow with state saving."""
        # Set up the mocks
        mock_fetch.return_value = sample_papers
        mock_filter.return_value = [sample_papers[0]]
        mock_store.return_value = None
        mock_send.return_value = True

        # Create a state file path
        state_file = os.path.join(os.path.dirname(temp_db_path), "scheduler_state.json")

        # Set parameters
        scheduler.set_search_parameters(query="quantum computing")
        scheduler.set_slack_webhook("https://hooks.slack.com/services/fake/webhook")
        scheduler.set_state_file(state_file)

        # Run harvest
        result = scheduler.run_harvest()

        # Verify the process and state saving
        assert result is True
        mock_fetch.assert_called_once()
        mock_filter.assert_called_once_with(sample_papers)
        mock_store.assert_called_once_with([sample_papers[0]])
        mock_send.assert_called_once_with([sample_papers[0]])
        mock_save.assert_called_once_with(state_file)

        # Clean up
        if os.path.exists(state_file):
            os.remove(state_file)
