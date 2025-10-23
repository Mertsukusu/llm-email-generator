"""
Web scraper for construction conference speakers with live + fallback support.
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from pathlib import Path
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Speaker

logger = logging.getLogger(__name__)


async def fetch_speakers(url: str, fallback_path: str = None) -> list[dict]:
    """
    Fetch speaker data from live URL with fallback to local HTML file.
    
    Args:
        url: Conference speakers URL
        fallback_path: Path to local HTML file as fallback
        
    Returns:
        List of speaker dictionaries with keys: name, title, company
    """
    speakers = []
    
    # Try live scraping first
    try:
        speakers = await _scrape_live_url(url)
        if speakers:
            logger.info(f"Successfully scraped {len(speakers)} speakers from live URL")
            return speakers
    except Exception as e:
        logger.warning(f"Live scraping failed: {e}")
    
    # Fallback to local file
    if fallback_path and Path(fallback_path).exists():
        try:
            speakers = await _scrape_local_file(fallback_path)
            logger.info(f"Successfully scraped {len(speakers)} speakers from local file")
            return speakers
        except Exception as e:
            logger.error(f"Local file scraping failed: {e}")
    
    logger.error("Both live and local scraping failed")
    return []


async def _scrape_live_url(url: str) -> list[dict]:
    """Scrape speakers from live URL."""
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            html = await response.text()
            return _parse_speakers_html(html)


async def _scrape_local_file(file_path: str) -> list[dict]:
    """Scrape speakers from local HTML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return _parse_speakers_html(html)


def _parse_speakers_html(html: str) -> list[dict]:
    """
    Parse speaker data from HTML content.
    
    Expected HTML structure (adapt as needed):
    - Speaker cards with name, title, company
    - Common selectors: .speaker, .speaker-card, etc.
    """
    soup = BeautifulSoup(html, 'html.parser')
    speakers = []
    
    # Try multiple possible selectors for speaker cards
    speaker_selectors = [
        '.speaker',
        '.speaker-card', 
        '.speaker-item',
        '.speaker-profile',
        '[class*="speaker"]'
    ]
    
    speaker_elements = []
    for selector in speaker_selectors:
        elements = soup.select(selector)
        if elements:
            speaker_elements = elements
            logger.info(f"Found {len(elements)} speakers using selector: {selector}")
            break
    
    if not speaker_elements:
        # Fallback: look for any elements that might contain speaker info
        speaker_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'speaker' in x.lower())
        logger.info(f"Fallback found {len(speaker_elements)} potential speaker elements")
    
    for element in speaker_elements:
        try:
            speaker_data = _extract_speaker_data(element)
            if speaker_data and all(speaker_data.values()):
                # Validate speaker data with Pydantic
                try:
                    validated_speaker = Speaker(**speaker_data)
                    speakers.append(speaker_data)
                except Exception as validation_error:
                    logger.warning(f"Invalid speaker data: {validation_error}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to extract speaker data: {e}")
            continue
    
    return speakers


def _extract_speaker_data(element) -> dict:
    """Extract name, title, and company from a speaker element."""
    # Try multiple selectors for each field
    name_selectors = ['h3', 'h4', '.name', '.speaker-name', '[class*="name"]']
    title_selectors = ['.title', '.position', '.role', '[class*="title"]', '[class*="position"]']
    company_selectors = ['.company', '.organization', '[class*="company"]', '[class*="org"]']
    
    name = _extract_text_by_selectors(element, name_selectors)
    title = _extract_text_by_selectors(element, title_selectors)
    company = _extract_text_by_selectors(element, company_selectors)
    
    # Clean up the extracted text
    name = _clean_text(name)
    title = _clean_text(title)
    company = _clean_text(company)
    
    return {
        'name': name,
        'title': title,
        'company': company
    }


def _extract_text_by_selectors(element, selectors: list[str]) -> str:
    """Try multiple selectors to extract text from an element."""
    for selector in selectors:
        found = element.select_one(selector)
        if found:
            return found.get_text(strip=True)
    return ""


def _clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove common prefixes/suffixes
    text = text.replace('Speaker:', '').replace('Name:', '').strip()
    
    return text
