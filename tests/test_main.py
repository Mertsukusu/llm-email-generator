"""
Unit tests for main application logic.
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import api_call_with_retry


class TestMainLogic:
    """Test cases for main application logic."""
    
    @pytest.mark.asyncio
    async def test_api_call_with_retry_success(self):
        """Test successful API call without retries."""
        async def mock_func():
            return "success"
        
        result = await api_call_with_retry(mock_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_api_call_with_retry_quota_error_success(self):
        """Test API call with quota error that succeeds on retry."""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 You exceeded your current quota")
            return "success"
        
        result = await api_call_with_retry(mock_func)
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_api_call_with_retry_max_retries_exceeded(self):
        """Test API call that fails after max retries."""
        async def mock_func():
            raise Exception("429 You exceeded your current quota")
        
        with pytest.raises(Exception, match="429 You exceeded your current quota"):
            await api_call_with_retry(mock_func)
    
    @pytest.mark.asyncio
    async def test_api_call_with_retry_non_quota_error(self):
        """Test API call with non-quota error (should not retry)."""
        async def mock_func():
            raise Exception("500 Internal Server Error")
        
        with pytest.raises(Exception, match="500 Internal Server Error"):
            await api_call_with_retry(mock_func)
    
    # Note: process_speaker function is defined inside main() and not accessible for testing
    # These tests would require refactoring the main.py to extract process_speaker as a separate function
