"""
Unit tests for categorizer functionality.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.categorizer import (
    categorize_company, 
    is_target_category, 
    _classify_by_keywords,
    COMPETITORS,
    PARTNERS
)


class TestCategorizer:
    """Test cases for categorizer functionality."""
    
    def test_manual_competitor_detection(self):
        """Test manual competitor list detection."""
        # Test direct company name match
        assert "Propeller" in COMPETITORS
        assert "DJI" in COMPETITORS
        assert "Pix4D" in COMPETITORS
        
        # Test case insensitive matching
        assert any("propeller" in comp.lower() for comp in COMPETITORS)
        assert any("dji" in comp.lower() for comp in COMPETITORS)
    
    def test_manual_partner_detection(self):
        """Test manual partner list detection."""
        # Test direct company name match
        assert "Autodesk" in PARTNERS
        assert "Microsoft" in PARTNERS
        assert "Google" in PARTNERS
        
        # Test case insensitive matching
        assert any("autodesk" in partner.lower() for partner in PARTNERS)
        assert any("microsoft" in partner.lower() for partner in PARTNERS)
    
    def test_classify_by_keywords_builder(self):
        """Test keyword-based classification for Builder category."""
        # Test builder keywords
        assert _classify_by_keywords("Construction Manager") == "Builder"
        assert _classify_by_keywords("Project Manager") == "Builder"  # "project manager" is in keywords
        assert _classify_by_keywords("General Contractor") == "Builder"
        assert _classify_by_keywords("Architect") == "Builder"
        assert _classify_by_keywords("Site Superintendent") == "Builder"
    
    def test_classify_by_keywords_owner(self):
        """Test keyword-based classification for Owner category."""
        # Test owner keywords
        assert _classify_by_keywords("Property Owner") == "Owner"
        assert _classify_by_keywords("Facility Manager") == "Owner"
        assert _classify_by_keywords("Asset Manager") == "Owner"
        assert _classify_by_keywords("Investment Manager") == "Owner"
        # Note: "Real Estate Developer" matches "developer" in BUILDER_KEYWORDS, so it gets classified as Builder
    
    def test_classify_by_keywords_other(self):
        """Test keyword-based classification for Other category."""
        # Test non-matching titles
        assert _classify_by_keywords("Software Engineer") == "Other"
        assert _classify_by_keywords("Marketing Director") == "Other"
        assert _classify_by_keywords("Sales Manager") == "Other"
        assert _classify_by_keywords("") == "Other"
    
    @pytest.mark.asyncio
    async def test_categorize_company_competitor_manual(self):
        """Test categorization of known competitors using manual list."""
        mock_gemini = AsyncMock()
        
        result = await categorize_company("Propeller Aero", "CEO", mock_gemini)
        assert result == "Competitor"
        
        result = await categorize_company("DJI Technologies", "Engineer", mock_gemini)
        assert result == "Competitor"
    
    @pytest.mark.asyncio
    async def test_categorize_company_partner_manual(self):
        """Test categorization of known partners using manual list."""
        mock_gemini = AsyncMock()
        
        result = await categorize_company("Autodesk Inc", "Product Manager", mock_gemini)
        assert result == "Partner"
        
        result = await categorize_company("Microsoft Corporation", "Developer", mock_gemini)
        assert result == "Partner"
    
    @pytest.mark.asyncio
    async def test_categorize_company_gemini_success(self):
        """Test categorization using Gemini API with successful response."""
        mock_gemini = AsyncMock()
        mock_response = AsyncMock()
        mock_response.text = "Builder"
        mock_gemini.generate_content_async.return_value = mock_response
        
        result = await categorize_company("ABC Construction", "Project Manager", mock_gemini)
        assert result == "Builder"
        mock_gemini.generate_content_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_categorize_company_gemini_failure_fallback(self):
        """Test categorization fallback when Gemini fails."""
        mock_gemini = AsyncMock()
        mock_gemini.generate_content_async.side_effect = Exception("API Error")
        
        # Should fallback to keyword-based classification
        result = await categorize_company("ABC Construction", "Project Manager", mock_gemini)
        assert result == "Builder"  # Based on "Project Manager" title
    
    @pytest.mark.asyncio
    async def test_categorize_company_gemini_invalid_response(self):
        """Test categorization when Gemini returns invalid response."""
        mock_gemini = AsyncMock()
        mock_response = AsyncMock()
        mock_response.text = "InvalidCategory"
        mock_gemini.generate_content_async.return_value = mock_response
        
        # Should fallback to keyword-based classification
        result = await categorize_company("ABC Construction", "Project Manager", mock_gemini)
        assert result == "Builder"  # Based on "Project Manager" title
    
    def test_is_target_category(self):
        """Test target category filtering."""
        assert is_target_category("Builder") == True
        assert is_target_category("Owner") == True
        assert is_target_category("Competitor") == False
        assert is_target_category("Partner") == False
        assert is_target_category("Other") == False
        assert is_target_category("") == False
    
    @pytest.mark.asyncio
    async def test_categorize_company_empty_inputs(self):
        """Test categorization with empty inputs."""
        mock_gemini = AsyncMock()
        
        result = await categorize_company("", "CEO", mock_gemini)
        assert result == "Other"
        
        result = await categorize_company("ABC Corp", "", mock_gemini)
        assert result == "Other"
        
        result = await categorize_company("", "", mock_gemini)
        assert result == "Other"
