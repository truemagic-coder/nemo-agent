import pytest
from news_scraper_604.scraper import get_headlines
from unittest.mock import patch, MagicMock

@patch('requests.get')
def test_get_headlines(mock_get):
    """Test the get_headlines function with mocked response."""
    mock_response = MagicMock()
    mock_response.text = '<html><body><h3>Headline 1</h3><h3>Headline 2</h3></body></html>'
    mock_get.return_value = mock_response

    assert get_headlines('http://test.com') == ['Headline 1', 'Headline 2']
