"""
Email content generator using Google Gemini 2.5 Flash.
"""
import logging
from typing import Dict, Any
import sys
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

logger = logging.getLogger(__name__)


async def generate_email(speaker_data: Dict[str, Any], category: str, gemini_client) -> Dict[str, str]:
    """
    Generate personalized email subject and body for a speaker.
    
    Args:
        speaker_data: Dict with keys: name, title, company
        category: Company category (Builder/Owner)
        gemini_client: Google Gemini client instance
        
    Returns:
        Dict with keys: subject, body
    """
    name = speaker_data.get('name', '')
    title = speaker_data.get('title', '')
    company = speaker_data.get('company', '')
    
    try:
        # Generate subject and body in one call for consistency
        email_content = await _generate_email_content(name, title, company, category, gemini_client)
        return email_content
    except Exception as e:
        logger.error(f"Email generation failed for {name}: {e}")
        # Return fallback email
        return _generate_fallback_email(name, title, company, category)


@retry(
    stop=stop_after_attempt(config.RETRY_STOP_AFTER_ATTEMPT),
    wait=wait_exponential(multiplier=config.RETRY_WAIT_EXPONENTIAL_MULTIPLIER, max=config.RETRY_WAIT_EXPONENTIAL_MAX),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def _generate_email_content(name: str, title: str, company: str, category: str, gemini_client) -> Dict[str, str]:
    """Generate email content using Gemini."""
    
    # Craft detailed prompt based on category
    if category == "Builder":
        role_context = "construction professionals who build and manage projects"
        value_props = "aerial intelligence for construction progress tracking, site management, and project oversight"
    elif category == "Owner":
        role_context = "property owners and developers who commission construction projects"
        value_props = "aerial intelligence for project monitoring, progress verification, and asset management"
    else:
        role_context = "construction industry professionals"
        value_props = "aerial intelligence for construction and site management"
    
    prompt = f"""
You are writing a personalized email to invite a construction conference speaker to visit DroneDeploy's booth #42.

Speaker Details:
- Name: {name}
- Title: {title} 
- Company: {company}
- Category: {category} ({role_context})

Requirements:
1. Subject line: Create an interesting hook that would appeal to their specific role and industry
2. Email body: 2-3 sentences that:
   - Mention why DroneDeploy is relevant to their business/role
   - Invite them to booth #42 for a demo
   - Mention they'll receive a free gift
   - Keep it professional but engaging

DroneDeploy Value Props to Consider:
- {value_props}
- Drone-based aerial mapping and surveying
- Construction progress tracking and documentation
- Site safety and compliance monitoring
- Integration with construction management software

Format your response as:
SUBJECT: [subject line here]
BODY: [email body here]
"""

    try:
        response = await gemini_client.generate_content_async(prompt)
        content = response.text.strip()
        
        # Parse the response
        subject, body = _parse_email_response(content)
        
        if subject and body:
            return {"subject": subject, "body": body}
        else:
            logger.warning(f"Failed to parse Gemini response for {name}")
            return _generate_fallback_email(name, title, company, category)
            
    except Exception as e:
        logger.error(f"Gemini email generation error for {name}: {e}")
        raise  # Re-raise to trigger retry


def _parse_email_response(content: str) -> tuple[str, str]:
    """Parse subject and body from Gemini response."""
    lines = content.split('\n')
    subject = ""
    body = ""
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('SUBJECT:'):
            subject = line.replace('SUBJECT:', '').strip()
            current_section = 'subject'
        elif line.startswith('BODY:'):
            body = line.replace('BODY:', '').strip()
            current_section = 'body'
        elif current_section == 'body' and line:
            # Continue building body from subsequent lines
            body += ' ' + line
    
    return subject, body


def _generate_fallback_email(name: str, title: str, company: str, category: str) -> Dict[str, str]:
    """Generate a simple fallback email when Gemini fails."""
    
    if category == "Builder":
        subject = f"See how {company} can streamline construction with aerial intelligence"
        body = f"Hi {name}, as a {title} at {company}, you know how important it is to track construction progress efficiently. DroneDeploy's aerial intelligence platform helps construction teams like yours monitor projects, ensure safety compliance, and deliver on time. Stop by our booth #42 for a personalized demo and receive a free gift!"
    elif category == "Owner":
        subject = f"Monitor your {company} construction investments with aerial intelligence"
        body = f"Hi {name}, as a {title} at {company}, you understand the value of transparent project oversight. DroneDeploy provides property owners and developers with real-time aerial insights to verify progress, ensure quality, and protect your investments. Visit booth #42 for a demo and free gift!"
    else:
        subject = f"Discover how {company} can benefit from construction aerial intelligence"
        body = f"Hi {name}, DroneDeploy's aerial intelligence platform is transforming how construction professionals manage projects and sites. As a {title} at {company}, you'll see immediate value in our progress tracking and site management capabilities. Stop by booth #42 for a demo and free gift!"
    
    return {"subject": subject, "body": body}
