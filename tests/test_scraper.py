"""
Unit tests for scraper functionality.
"""
import pytest
import asyncio
from unittest.mock import patch, mock_open
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scraper import fetch_speakers, _parse_speakers_html, _extract_speaker_data, _clean_text


class TestScraper:
    """Test cases for scraper functionality."""
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        assert _clean_text("  John   Smith  ") == "John Smith"
        assert _clean_text("Speaker: Jane Doe") == "Jane Doe"
        assert _clean_text("") == ""
        assert _clean_text("Name: Test User") == "Test User"
    
    def test_extract_speaker_data(self):
        """Test speaker data extraction from HTML elements."""
        from bs4 import BeautifulSoup
        
        # Mock HTML element
        html = """
        <div class="speaker">
            <h3>John Smith</h3>
            <p class="title">CEO</p>
            <p class="company">ABC Construction</p>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div', class_='speaker')
        
        result = _extract_speaker_data(element)
        
        assert result['name'] == "John Smith"
        assert result['title'] == "CEO"
        assert result['company'] == "ABC Construction"
    
    def test_parse_speakers_html_with_valid_data(self):
        """Test parsing HTML with valid speaker data."""
        html = """
        <html>
            <body>
                <div class="speaker">
                    <h3>John Smith</h3>
                    <p class="title">CEO</p>
                    <p class="company">ABC Construction</p>
                </div>
                <div class="speaker">
                    <h3>Jane Doe</h3>
                    <p class="title">Project Manager</p>
                    <p class="company">XYZ Engineering</p>
                </div>
            </body>
        </html>
        """
        
        speakers = _parse_speakers_html(html)
        
        assert len(speakers) == 2
        assert speakers[0]['name'] == "John Smith"
        assert speakers[0]['title'] == "CEO"
        assert speakers[0]['company'] == "ABC Construction"
        assert speakers[1]['name'] == "Jane Doe"
    
    def test_parse_speakers_html_with_empty_data(self):
        """Test parsing HTML with no speaker data."""
        html = "<html><body><div>No speakers here</div></body></html>"
        speakers = _parse_speakers_html(html)
        assert len(speakers) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_speakers_with_local_file(self):
        """Test fetching speakers from local HTML file."""
        # Mock HTML content
        mock_html = """
        <html>
            <body>
                <div class="speaker">
                    <h3>Test Speaker</h3>
                    <p class="title">Test Title</p>
                    <p class="company">Test Company</p>
                </div>
            </body>
        </html>
        """
        
        # Mock file operations
        with patch("builtins.open", mock_open(read_data=mock_html)):
            with patch("pathlib.Path.exists", return_value=True):
                speakers = await fetch_speakers("http://fake-url.com", "test.html")
                
                assert len(speakers) == 1
                assert speakers[0]['name'] == "Test Speaker"
                assert speakers[0]['title'] == "Test Title"
                assert speakers[0]['company'] == "Test Company"
    
    @pytest.mark.asyncio
    async def test_fetch_speakers_live_url_fallback(self):
        """Test fallback to local file when live URL fails."""
        mock_html = """
        <html>
            <body>
                <div class="speaker">
                    <h3>Fallback Speaker</h3>
                    <p class="title">Fallback Title</p>
                    <p class="company">Fallback Company</p>
                </div>
            </body>
        </html>
        """
        
        # Mock live URL failure and local file success
        with patch("utils.scraper._scrape_live_url", side_effect=Exception("Network error")):
            with patch("builtins.open", mock_open(read_data=mock_html)):
                with patch("pathlib.Path.exists", return_value=True):
                    speakers = await fetch_speakers("http://fake-url.com", "test.html")
                    
                    assert len(speakers) == 1
                    assert speakers[0]['name'] == "Fallback Speaker"
    
    @pytest.mark.asyncio
    async def test_fetch_speakers_both_fail(self):
        """Test when both live URL and local file fail."""
        with patch("utils.scraper._scrape_live_url", side_effect=Exception("Network error")):
            with patch("pathlib.Path.exists", return_value=False):
                speakers = await fetch_speakers("http://fake-url.com", "nonexistent.html")
                assert len(speakers) == 0
