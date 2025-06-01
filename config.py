import os
from dotenv import load_dotenv
 
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-pro"

# Scraper Config
MAX_COMMENTS_PER_POST = 300
REQUEST_TIMEOUT = 30 #seconds
USER_AGENT_ROTATION = True
HEADLESS_BROWSER = True

# Rate Limiting
INITIAL_DELAY = 2 #seconds
MAX_DELAY = 10 #seconds
RATE_LIMIT_FACTOR = 1.5

# Proxy Config
USE_PROXIES = False # Set to True if using proxies
PROXY_ROTATION_FREQUENCY = 10

# Pattern storage
PATTERN_STORAGE_PATH = "data/patterns/facebook_patterns.json"

# Output configuration
OUTPUT_DIR = "data/output"
OUTPUT_FORMAT = "csv" # Options: csv, json

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "scraper.log"