"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.text = "Builder"
    client.generate_content_async.return_value = mock_response
    return client


@pytest.fixture
def sample_speaker_data():
    """Sample speaker data for testing."""
    return {
        'name': 'John Smith',
        'title': 'CEO',
        'company': 'ABC Construction'
    }


@pytest.fixture
def sample_speakers():
    """Sample speakers list for testing."""
    return [
        {
            'name': 'John Smith',
            'title': 'CEO',
            'company': 'ABC Construction'
        },
        {
            'name': 'Jane Doe',
            'title': 'Project Manager',
            'company': 'XYZ Engineering'
        }
    ]


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
