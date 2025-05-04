"""Tests for the Notify module."""

import pytest
from unittest.mock import patch
import json

# Import the module we'll be testing
from src.arxiv_harvester.notify.slack import SlackNotifier


class TestSlackNotifier:
    """Test suite for the SlackNotifier class."""

    @pytest.fixture
    def notifier(self):
        """Fixture to create a SlackNotifier instance."""
        return SlackNotifier()

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

    # Test 1: Test initialization
    def test_init(self, notifier):
        """Test initialization of SlackNotifier."""
        assert isinstance(notifier, SlackNotifier)

    # Test 2: Test message formatting for a single paper
    def test_format_paper_message(self, notifier, sample_papers):
        """Test formatting a message for a single paper."""
        paper = sample_papers[0]
        message = notifier.format_paper_message(paper)

        # Check that the message contains essential information
        assert paper['title'] in message
        assert paper['summary'] in message
        assert paper['pdf_url'] in message
        for author in paper['authors']:
            assert author in message

    # Test 3: Test message formatting for multiple papers
    def test_format_papers_message(self, notifier, sample_papers):
        """Test formatting a message for multiple papers."""
        message = notifier.format_papers_message(sample_papers)

        # Check that the message contains information from both papers
        assert sample_papers[0]['title'] in message
        assert sample_papers[1]['title'] in message

    # Test 4: Test successful posting to Slack
    @patch('requests.post')
    def test_post_to_slack_success(self, mock_post, notifier, sample_papers):
        """Test successfully posting to Slack."""
        # Mock successful response
        mock_post.return_value.status_code = 200

        # Call the method
        result = notifier.post_papers_to_slack(sample_papers, 'https://hooks.slack.com/services/fake/webhook')

        # Verify the result
        assert result is True
        mock_post.assert_called_once()

        # Verify the payload
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        assert 'text' in payload
        assert sample_papers[0]['title'] in payload['text']

    # Test 5: Test handling of failed posting to Slack
    @patch('requests.post')
    def test_post_to_slack_failure(self, mock_post, notifier, sample_papers):
        """Test handling of failed Slack posting."""
        # Mock failed response
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Bad Request'

        # Call the method
        result = notifier.post_papers_to_slack(sample_papers, 'https://hooks.slack.com/services/fake/webhook')

        # Verify the result
        assert result is False

    # Test 6: Test handling of exception during posting
    @patch('requests.post')
    def test_post_to_slack_exception(self, mock_post, notifier, sample_papers):
        """Test handling of exception during Slack posting."""
        # Mock an exception
        mock_post.side_effect = Exception('Connection error')

        # Call the method
        result = notifier.post_papers_to_slack(sample_papers, 'https://hooks.slack.com/services/fake/webhook')

        # Verify the result
        assert result is False

    # Test 7: Test posting with custom message
    @patch('requests.post')
    def test_post_to_slack_custom_message(self, mock_post, notifier):
        """Test posting a custom message to Slack."""
        # Mock successful response
        mock_post.return_value.status_code = 200

        # Call the method with a custom message
        custom_message = 'Custom message for testing'
        result = notifier.post_message_to_slack(custom_message, 'https://hooks.slack.com/services/fake/webhook')

        # Verify the result
        assert result is True
        mock_post.assert_called_once()

        # Verify the payload
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        assert payload['text'] == custom_message

    # Test 8: Test message truncation for long messages
    def test_message_truncation(self, notifier):
        """Test that long messages are truncated."""
        # Create a very long message
        long_message = 'A' * 10000

        # Format the long message
        truncated = notifier.truncate_message(long_message)

        # Verify the message was truncated
        assert len(truncated) < len(long_message)
        assert '... (message truncated)' in truncated

    # Test 9: Test formatting with blocks for rich messages
    def test_format_with_blocks(self, notifier, sample_papers):
        """Test formatting a message with Slack blocks for rich formatting."""
        paper = sample_papers[0]
        blocks = notifier.format_paper_blocks(paper)

        # Verify blocks structure
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert blocks[0]['type'] == 'header'

        # Verify content in blocks
        block_text = json.dumps(blocks)
        assert paper['title'] in block_text
        assert paper['pdf_url'] in block_text

    # Test 10: Test posting with blocks format
    @patch('requests.post')
    def test_post_with_blocks(self, mock_post, notifier, sample_papers):
        """Test posting with Slack blocks format."""
        # Mock successful response
        mock_post.return_value.status_code = 200

        # Call the method with blocks=True
        result = notifier.post_papers_to_slack(sample_papers, 'https://hooks.slack.com/services/fake/webhook', use_blocks=True)

        # Verify the result
        assert result is True
        mock_post.assert_called_once()

        # Verify the payload contains blocks
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        assert 'blocks' in payload

    # Test 11: Test handling of empty paper list
    @patch('requests.post')
    def test_handle_empty_paper_list(self, mock_post, notifier):
        """Test handling of empty paper list."""
        # Call the method with an empty list
        result = notifier.post_papers_to_slack([], 'https://hooks.slack.com/services/fake/webhook')

        # Verify no request was made and the result is False
        mock_post.assert_not_called()
        assert result is False

    # Test 12: Test custom pre/post message
    def test_custom_pre_post_message(self, notifier, sample_papers):
        """Test adding custom pre/post messages."""
        pre_message = "Here are the latest papers:"
        post_message = "Check them out!"

        message = notifier.format_papers_message(
            sample_papers, pre_message=pre_message, post_message=post_message
        )

        # Verify pre/post messages are included
        assert message.startswith(pre_message)
        assert message.endswith(post_message)

    # Test 13: Test category highlighting
    def test_category_highlighting(self, notifier):
        """Test highlighting of specific categories."""
        # Paper with important category
        paper = {
            'id': 'http://arxiv.org/abs/2104.12345',
            'title': 'Important Paper',
            'summary': 'This is important.',
            'authors': ['Author One'],
            'published_date': '2021-04-15T00:00:00Z',
            'pdf_url': 'http://arxiv.org/pdf/2104.12345',
            'category': 'cs.AI'
        }

        # Set important categories
        notifier.set_important_categories(['cs.AI', 'cs.CL'])

        # Format message
        message = notifier.format_paper_message(paper)

        # Verify highlighting
        assert "*IMPORTANT*" in message or "[IMPORTANT]" in message

    # Test 14: Test maximum papers limit
    def test_max_papers_limit(self, notifier):
        """Test limiting the number of papers in a message."""
        # Create many papers
        many_papers = [{
            'id': f'http://arxiv.org/abs/{2104 + i}',
            'title': f'Paper {i}',
            'summary': f'Abstract {i}',
            'authors': [f'Author {i}'],
            'published_date': f'2021-04-{i + 1:02d}T00:00:00Z',
            'pdf_url': f'http://arxiv.org/pdf/{2104 + i}'
        } for i in range(20)]

        # Format with a limit
        message = notifier.format_papers_message(many_papers, max_papers=5)

        # Count papers in message
        paper_count = message.count("Title:")
        assert paper_count == 5
        assert "Showing 5 of 20 papers" in message

    # Test 15: Test message with markdown formatting
    def test_markdown_formatting(self, notifier, sample_papers):
        """Test markdown formatting in messages."""
        paper = sample_papers[0]

        # Enable markdown formatting
        notifier.set_use_markdown(True)

        # Format message
        message = notifier.format_paper_message(paper)

        # Check for markdown elements
        assert "**Title:**" in message or "*Title:*" in message
        assert "[PDF]" in message
