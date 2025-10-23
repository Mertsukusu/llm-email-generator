"""
Company categorization using manual lists + Google Gemini 2.5 Flash.
"""
import logging
from typing import Optional
import sys
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

logger = logging.getLogger(__name__)

# Import from config
COMPETITORS = config.COMPETITORS
PARTNERS = config.PARTNERS
BUILDER_KEYWORDS = config.BUILDER_KEYWORDS
OWNER_KEYWORDS = config.OWNER_KEYWORDS


async def categorize_company(company: str, title: str, gemini_client) -> str:
    """
    Categorize a company as Builder, Owner, Partner, Competitor, or Other.
    
    Args:
        company: Company name
        title: Person's job title
        gemini_client: Google Gemini client instance
        
    Returns:
        Category string: "Builder", "Owner", "Partner", "Competitor", or "Other"
    """
    if not company or not title:
        return "Other"
    
    # Check manual lists first
    company_lower = company.lower()
    title_lower = title.lower()
    
    # Check competitors
    for competitor in COMPETITORS:
        if competitor.lower() in company_lower or competitor.lower() in title_lower:
            logger.info(f"Classified {company} as Competitor (manual list)")
            return "Competitor"
    
    # Check partners
    for partner in PARTNERS:
        if partner.lower() in company_lower or partner.lower() in title_lower:
            logger.info(f"Classified {company} as Partner (manual list)")
            return "Partner"
    
    # Use Gemini for remaining classifications
    try:
        category = await _classify_with_gemini(company, title, gemini_client)
        logger.info(f"Classified {company} as {category} (Gemini)")
        return category
    except Exception as e:
        logger.warning(f"Gemini classification failed for {company}: {e}")
        # Fallback to keyword-based classification
        return _classify_by_keywords(title)


@retry(
    stop=stop_after_attempt(config.RETRY_STOP_AFTER_ATTEMPT),
    wait=wait_exponential(multiplier=config.RETRY_WAIT_EXPONENTIAL_MULTIPLIER, max=config.RETRY_WAIT_EXPONENTIAL_MAX),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def _classify_with_gemini(company: str, title: str, gemini_client) -> str:
    """Use Gemini to classify company based on name and person's title."""
    
    prompt = f"""
You are a construction industry expert. Classify this company and person into one of these categories:

- Builder: Companies that build things (contractors, engineering firms, construction companies, architects, etc.)
- Owner: Companies that own/commission construction projects (real estate developers, property owners, facility managers, etc.)
- Other: Any other type of company not clearly in the above categories

Company: {company}
Person's Title: {title}

Respond with ONLY one word: Builder, Owner, or Other
"""

    try:
        response = await gemini_client.generate_content_async(prompt)
        category = response.text.strip().title()
        
        # Validate response
        if category in ["Builder", "Owner", "Other"]:
            return category
        else:
            logger.warning(f"Invalid Gemini response: {category}")
            return _classify_by_keywords(title)
            
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise  # Re-raise to trigger retry


def _classify_by_keywords(title: str) -> str:
    """Fallback classification using keyword matching."""
    title_lower = title.lower()
    
    # Check for builder keywords
    for keyword in BUILDER_KEYWORDS:
        if keyword in title_lower:
            return "Builder"
    
    # Check for owner keywords  
    for keyword in OWNER_KEYWORDS:
        if keyword in title_lower:
            return "Owner"
    
    # Default to Other if no keywords match
    return "Other"


def is_target_category(category: str) -> bool:
    """
    Check if category should be included in email generation.
    Only Builder and Owner categories are targets.
    """
    return category in config.TARGET_CATEGORIES
