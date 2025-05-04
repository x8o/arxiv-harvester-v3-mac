"""Tests for the arXiv API client."""

import pytest
import requests
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json
import os

# Import the module we'll be testing (we'll create this file soon)
from src.arxiv_harvester.api.client import ArxivApiClient


class TestArxivApiClient:
    """Test suite for the ArxivApiClient class."""

    @pytest.fixture
    def api_client(self):
        """Fixture to create an instance of ArxivApiClient."""
        return ArxivApiClient()
    
    @pytest.fixture
    def sample_response(self):
        """Fixture to provide a sample API response."""
        # Load a sample response from a file if it exists, otherwise use a basic mock
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'arxiv_response.json')
        if os.path.exists(fixture_path):
            with open(fixture_path, 'r') as f:
                return json.load(f)
        else:
            # Basic mock response
            return {
                'feed': {
                    'entry': [
                        {
                            'id': 'http://arxiv.org/abs/2104.12345',
                            'title': 'Sample Paper Title',
                            'summary': 'This is a sample abstract.',
                            'author': [{'name': 'Author One'}, {'name': 'Author Two'}],
                            'published': '2021-04-15T00:00:00Z',
                            'link': [{'href': 'http://arxiv.org/pdf/2104.12345'}]
                        }
                    ]
                }
            }
    
    # Test 1: Verify initialization with default parameters
    def test_init_default_parameters(self, api_client):
        """Test that the client initializes with correct default parameters."""
        assert api_client.base_url == 'http://export.arxiv.org/api/query'
        assert api_client.delay == 3.0  # Default rate limiting delay
        assert api_client.timeout == 30  # Default timeout
    
    # Test 2: Verify initialization with custom parameters
    def test_init_custom_parameters(self):
        """Test that the client can be initialized with custom parameters."""
        client = ArxivApiClient(delay=5.0, timeout=60)
        assert client.base_url == 'http://export.arxiv.org/api/query'
        assert client.delay == 5.0
        assert client.timeout == 60
    
    # Test 3: Test search with basic query
    @patch('requests.get')
    def test_search_basic_query(self, mock_get, api_client, sample_response):
        """Test basic search query functionality."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        results = api_client.search(query='machine learning')
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'machine learning' in mock_get.call_args[0][0]
        
        # Verify the results are processed correctly
        assert len(results) > 0
        assert 'title' in results[0]
        assert 'id' in results[0]
    
    # Test 4: Test search with category filter
    @patch('requests.get')
    def test_search_with_category(self, mock_get, api_client, sample_response):
        """Test search with category filter."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        results = api_client.search(query='neural networks', category='cs.AI')
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'neural networks' in mock_get.call_args[0][0]
        assert 'cat:cs.AI' in mock_get.call_args[0][0]
    
    # Test 5: Test search with date range
    @patch('requests.get')
    def test_search_with_date_range(self, mock_get, api_client, sample_response):
        """Test search with date range filter."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        results = api_client.search(
            query='reinforcement learning',
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'reinforcement learning' in mock_get.call_args[0][0]
        assert 'submittedDate:' in mock_get.call_args[0][0]
    
    # Test 6: Test search with max results
    @patch('requests.get')
    def test_search_with_max_results(self, mock_get, api_client, sample_response):
        """Test search with max results parameter."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        results = api_client.search(query='deep learning', max_results=50)
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'deep learning' in mock_get.call_args[0][0]
        assert 'max_results=50' in mock_get.call_args[0][0]
    
    # Test 7: Test search with sorting
    @patch('requests.get')
    def test_search_with_sorting(self, mock_get, api_client, sample_response):
        """Test search with sorting parameter."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        results = api_client.search(query='quantum computing', sort_by='lastUpdatedDate')
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'quantum computing' in mock_get.call_args[0][0]
        assert 'sortBy=lastUpdatedDate' in mock_get.call_args[0][0]
    
    # Test 8: Test search with sorting order
    @patch('requests.get')
    def test_search_with_sorting_order(self, mock_get, api_client, sample_response):
        """Test search with sorting order parameter."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        results = api_client.search(query='natural language processing', 
                                   sort_by='submittedDate', 
                                   sort_order='descending')
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert 'natural language processing' in mock_get.call_args[0][0]
        assert 'sortBy=submittedDate' in mock_get.call_args[0][0]
        assert 'sortOrder=descending' in mock_get.call_args[0][0]
    
    # Test 9: Test handling of API error
    @patch('requests.get')
    def test_handle_api_error(self, mock_get, api_client):
        """Test proper handling of API errors."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.content = b'Internal Server Error'
        
        with pytest.raises(Exception) as excinfo:
            api_client.search(query='error test')
        
        assert "API request failed" in str(excinfo.value)
    
    # Test 10: Test handling of connection error
    @patch('requests.get')
    def test_handle_connection_error(self, mock_get, api_client):
        """Test proper handling of connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(requests.exceptions.ConnectionError):
            api_client.search(query='connection test')
    
    # Test 11: Test handling of timeout error
    @patch('requests.get')
    def test_handle_timeout_error(self, mock_get, api_client):
        """Test proper handling of timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(requests.exceptions.Timeout):
            api_client.search(query='timeout test')
    
    # Test 12: Test response parsing with malformed data
    @patch('requests.get')
    def test_handle_malformed_response(self, mock_get, api_client):
        """Test proper handling of malformed response data."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'Not a valid XML or JSON'
        
        with pytest.raises(Exception) as excinfo:
            api_client.search(query='malformed test')
        
        assert "Failed to parse response" in str(excinfo.value)
    
    # Test 13: Test rate limiting functionality
    @patch('requests.get')
    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep, mock_get, api_client, sample_response):
        """Test that rate limiting logic is applied between consecutive requests."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        api_client.search(query='first query')
        api_client.search(query='second query')  # Should trigger rate limiting
        
        # Verify that sleep was called between requests
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] == api_client.delay
    
    # Test 14: Test parsing of paper details
    @patch('requests.get')
    def test_parse_paper_details(self, mock_get, api_client, sample_response):
        """Test extraction of detailed paper information from response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        results = api_client.search(query='detail test')
        
        # Check that all expected fields are extracted
        paper = results[0]
        assert 'id' in paper
        assert 'title' in paper
        assert 'summary' in paper
        assert 'authors' in paper
        assert 'published_date' in paper
        assert 'pdf_url' in paper
    
    # Test 15: Test get_paper_by_id function
    @patch('requests.get')
    def test_get_paper_by_id(self, mock_get, api_client, sample_response):
        """Test retrieval of a specific paper by its arXiv ID."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = json.dumps(sample_response).encode('utf-8')
        
        # Prepare mock to capture the URL
        def side_effect(url, *args, **kwargs):
            mock_get.call_args = ((url,), kwargs)
            return mock_get.return_value
        mock_get.side_effect = side_effect
        
        paper_id = '2104.12345'
        paper = api_client.get_paper_by_id(paper_id)
        
        # Verify the API was called with the correct parameters
        mock_get.assert_called_once()
        assert f'id_list={paper_id}' in mock_get.call_args[0][0]
        
        # Verify paper details are extracted correctly
        assert paper['id'] == 'http://arxiv.org/abs/2104.12345'
        assert paper['title'] == 'Sample Paper Title: Deep Learning Approaches'
