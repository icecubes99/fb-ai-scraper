# utils/html_processor.py
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_comment_candidates(html):
    """Extract potential comment elements from HTML.
    
    Args:
        html (str): HTML content
        
    Returns:
        list: Potential comment elements
    """
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    
    # Common Facebook comment selectors
    selectors = [
        'div[role="article"]',
        'div.UFICommentContent',
        'div._4eek',
        'div.comment',
        'div[data-testid="UFI2Comment"]',
        'div.UFIComment',
        'div[data-testid="comment"]'
    ]
    
    # Try each selector
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            candidates.extend(elements)
            logger.info(f"Found {len(elements)} potential comments with selector '{selector}'")
    
    return candidates

def clean_comment_text(text):
    """Clean and normalize comment text.
    
    Args:
        text (str): Raw comment text
        
    Returns:
        str: Cleaned comment text
    """
    if not text:
        return ""
        
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common Facebook reaction indicators
    reactions = ["Like", "Reply", "Share", "See Translation"]
    for reaction in reactions:
        text = text.replace(f" {reaction}", "")
        
    return text.strip()