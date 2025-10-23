"""
Configuration management for DroneDeploy email generation system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = 'gemini-2.5-flash'

# Rate Limiting Configuration
MAX_CONCURRENT = 1  # Limit concurrent API calls for free tier
API_DELAY = 0.1  # Delay between API calls in seconds (minimal for fastest processing)
MAX_RETRIES = 3  # Maximum retry attempts for API calls

# Retry Configuration (for tenacity)
RETRY_STOP_AFTER_ATTEMPT = 3
RETRY_WAIT_EXPONENTIAL_MULTIPLIER = 2
RETRY_WAIT_EXPONENTIAL_MAX = 60

# URLs and Paths
CONFERENCE_URL = "https://www.digitalconstructionweek.com/all-speakers/"
FALLBACK_HTML = "in/speakers.html"
OUTPUT_DIR = "out"
OUTPUT_FILE = "email_list.csv"
OUTPUT_CSV = f"{OUTPUT_DIR}/{OUTPUT_FILE}"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Validation Configuration
REQUIRED_SPEAKER_FIELDS = ['name', 'title', 'company']
MIN_NAME_LENGTH = 2
MIN_TITLE_LENGTH = 2
MIN_COMPANY_LENGTH = 2

# Email Configuration
EMAIL_SUBJECT_MAX_LENGTH = 100
EMAIL_BODY_MAX_LENGTH = 1000

# Categories
TARGET_CATEGORIES = ["Builder", "Owner"]
EXCLUDED_CATEGORIES = ["Competitor", "Partner", "Other"]

# Manual Company Lists
COMPETITORS = [
    "Propeller", "DJI", "Skydio", "Pix4D", "Agisoft", "RealityCapture",
    "Bentley", "Autodesk Civil 3D", "Topcon", "Leica", "Trimble",
    "Hexagon", "Faro", "3DR", "Parrot", "Yuneec", "Autel"
]

PARTNERS = [
    "Autodesk", "Procore", "Trimble", "Bentley", "Oracle", "SAP",
    "Microsoft", "Google", "Amazon", "IBM", "Salesforce", "ServiceNow"
]

# Keywords for classification
BUILDER_KEYWORDS = [
    "contractor", "construction", "builder", "developer", "engineering",
    "architect", "design", "project manager", "superintendent", "foreman",
    "general contractor", "subcontractor", "specialty contractor"
]

OWNER_KEYWORDS = [
    "owner", "client", "investor", "developer", "property manager",
    "facility manager", "asset manager", "real estate", "investment"
]
