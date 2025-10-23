"""
Main orchestration for DroneDeploy email generation system.
"""
import asyncio
import logging
import os
import pandas as pd
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from utils.scraper import fetch_speakers
from utils.categorizer import categorize_company, is_target_category
from utils.email_generator import generate_email

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Global statistics tracking
class ExecutionStats:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_speakers_scanned = 0
        self.speakers_processed = 0
        self.category_counts = {
            'Builder': 0,
            'Owner': 0,
            'Competitor': 0,
            'Partner': 0,
            'Other': 0
        }
        self.api_errors = 0
        self.emails_generated = 0
        self.speakers_skipped = 0
        
    def start_timer(self):
        self.start_time = datetime.now()
        
    def stop_timer(self):
        self.end_time = datetime.now()
        
    def get_execution_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(0)
        
    def increment_category(self, category):
        if category in self.category_counts:
            self.category_counts[category] += 1
            
    def increment_api_error(self):
        self.api_errors += 1
        
    def increment_processed(self):
        self.speakers_processed += 1
        
    def increment_emails_generated(self):
        self.emails_generated += 1
        
    def increment_skipped(self):
        self.speakers_skipped += 1

# Global stats instance
stats = ExecutionStats()


async def api_call_with_retry(func, *args, **kwargs):
    """Wrapper for API calls with retry logic and rate limiting."""
    for attempt in range(config.MAX_RETRIES):
        try:
            # Add delay between API calls
            if attempt > 0:
                await asyncio.sleep(config.API_DELAY * attempt)
            
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < config.MAX_RETRIES - 1:
                    # Extract retry delay from error message if available
                    retry_delay = config.API_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"API quota exceeded, retrying in {retry_delay}s (attempt {attempt + 1}/{config.MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Max retries exceeded for API call: {e}")
                    raise
            else:
                logger.error(f"API call failed: {e}")
                raise
    
    return None


def print_execution_report():
    """Print a comprehensive execution report."""
    stats.stop_timer()
    execution_time = stats.get_execution_time()
    
    print("\n" + "="*80)
    print("📊 EXECUTION REPORT")
    print("="*80)
    
    # Timing information
    print(f"⏱️  Total Execution Time: {execution_time}")
    print(f"📅 Started: {stats.start_time.strftime('%Y-%m-%d %H:%M:%S') if stats.start_time else 'N/A'}")
    print(f"📅 Finished: {stats.end_time.strftime('%Y-%m-%d %H:%M:%S') if stats.end_time else 'N/A'}")
    print()
    
    # Speaker statistics
    print("👥 SPEAKER STATISTICS")
    print("-" * 40)
    print(f"📊 Total Speakers Scanned: {stats.total_speakers_scanned}")
    print(f"🔄 Speakers Processed: {stats.speakers_processed}")
    print(f"✉️  Emails Generated: {stats.emails_generated}")
    print(f"⏭️  Speakers Skipped: {stats.speakers_skipped}")
    print()
    
    # Category breakdown
    print("🏷️  CATEGORY BREAKDOWN")
    print("-" * 40)
    for category, count in stats.category_counts.items():
        if count > 0:
            emoji = "🏗️" if category == "Builder" else "🏢" if category == "Owner" else "⚔️" if category == "Competitor" else "🤝" if category == "Partner" else "❓"
            print(f"{emoji} {category}: {count}")
    print()
    
    # API statistics
    print("🔌 API STATISTICS")
    print("-" * 40)
    print(f"❌ API Errors: {stats.api_errors}")
    if stats.speakers_processed > 0:
        success_rate = ((stats.speakers_processed - stats.api_errors) / stats.speakers_processed) * 100
        print(f"✅ Success Rate: {success_rate:.1f}%")
    print()
    
    # Performance metrics
    if stats.emails_generated > 0 and execution_time.total_seconds() > 0:
        emails_per_minute = (stats.emails_generated / execution_time.total_seconds()) * 60
        print("⚡ PERFORMANCE METRICS")
        print("-" * 40)
        print(f"📈 Emails per Minute: {emails_per_minute:.1f}")
        if stats.speakers_processed > 0:
            avg_time_per_speaker = execution_time.total_seconds() / stats.speakers_processed
            print(f"⏱️  Average Time per Speaker: {avg_time_per_speaker:.1f}s")
    print()
    
    # Summary
    print("📋 SUMMARY")
    print("-" * 40)
    if stats.emails_generated > 0:
        print(f"✅ Successfully generated {stats.emails_generated} personalized emails")
        print(f"📁 Output saved to: {config.OUTPUT_CSV}")
    else:
        print("⚠️  No emails were generated")
    
    if stats.api_errors > 0:
        print(f"⚠️  {stats.api_errors} API errors occurred during processing")
    
    print("="*80)


async def main():
    """Main async workflow for email generation."""
    
    # Start execution timer
    stats.start_timer()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Gemini client
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables")
        return
    
    genai.configure(api_key=api_key)
    gemini_client = genai.GenerativeModel(config.GEMINI_MODEL)
    
    logger.info("Starting DroneDeploy email generation system")
    
    # Step 1: Fetch speakers
    logger.info("Fetching speaker data...")
    speakers = await fetch_speakers(config.CONFERENCE_URL, config.FALLBACK_HTML)
    
    # Update statistics
    stats.total_speakers_scanned = len(speakers)
    
    if not speakers:
        logger.error("No speakers found. Exiting.")
        return
    
    logger.info(f"Found {len(speakers)} speakers")
    
    # Step 2: Process speakers concurrently (TEST MODE - only first 5)
    test_speakers = speakers[:5]  # TEST MODE: Only process first 5 speakers
    logger.info(f"TEST MODE: Processing only {len(test_speakers)} speakers instead of {len(speakers)}")
    
    # Create semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)
    
    async def process_speaker(speaker_data):
        """Process a single speaker: categorize + generate email."""
        async with semaphore:
            try:
                # Add delay between speakers to respect rate limits
                await asyncio.sleep(config.API_DELAY)
                
                # Categorize company with retry logic
                category = await api_call_with_retry(
                    categorize_company,
                    speaker_data['company'], 
                    speaker_data['title'], 
                    gemini_client
                )
                
                if not category:
                    logger.error(f"Failed to categorize {speaker_data['name']}")
                    stats.increment_api_error()
                    return None
                
                # Track category statistics
                stats.increment_category(category)
                stats.increment_processed()
                
                # Only generate emails for target categories
                if not is_target_category(category):
                    logger.info(f"Skipping {speaker_data['name']} - category: {category}")
                    stats.increment_skipped()
                    return None
                
                # Generate email with retry logic
                email_content = await api_call_with_retry(
                    generate_email,
                    speaker_data, 
                    category, 
                    gemini_client
                )
                
                if not email_content:
                    logger.error(f"Failed to generate email for {speaker_data['name']}")
                    stats.increment_api_error()
                    return None
                
                # Track successful email generation
                stats.increment_emails_generated()
                
                return {
                    'Speaker Name': speaker_data['name'],
                    'Speaker Title': speaker_data['title'],
                    'Speaker Company': speaker_data['company'],
                    'Company Category': category,
                    'Email Subject': email_content['subject'],
                    'Email Body': email_content['body']
                }
                
            except Exception as e:
                logger.error(f"Failed to process {speaker_data.get('name', 'Unknown')}: {e}")
                stats.increment_api_error()
                return None
    
    # Process all speakers concurrently (TEST MODE)
    tasks = [process_speaker(speaker) for speaker in test_speakers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    logger.info(f"Successfully processed {len(valid_results)} target speakers")
    
    # Step 3: Save to CSV
    if valid_results:
        logger.info(f"Saving results to {config.OUTPUT_CSV}")
        
        # Ensure output directory exists
        Path(config.OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame and save
        df = pd.DataFrame(valid_results)
        df.to_csv(config.OUTPUT_CSV, index=False)
        
        logger.info(f"Saved {len(valid_results)} emails to {config.OUTPUT_CSV}")
        
        # Print summary
        category_counts = df['Company Category'].value_counts()
        logger.info("Category breakdown:")
        for category, count in category_counts.items():
            logger.info(f"  {category}: {count}")
    else:
        logger.warning("No valid results to save")
    
    # Print comprehensive execution report
    print_execution_report()


if __name__ == "__main__":
    asyncio.run(main())
