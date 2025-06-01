# utils/rate_limiter.py
import asyncio
import random
import time
from utils.logger import get_logger
from config import INITIAL_DELAY, MAX_DELAY, RATE_LIMIT_FACTOR

logger = get_logger(__name__)

# Global variables to track rate limiting
last_request_time = 0
current_delay = INITIAL_DELAY
consecutive_errors = 0

async def adaptive_delay():
    """Implement adaptive rate limiting based on response patterns.
    
    This function adjusts delay times based on previous request success/failure.
    """
    global last_request_time, current_delay, consecutive_errors
    
    # Calculate time since last request
    now = time.time()
    time_since_last = now - last_request_time
    
    # If we've made a request recently, wait
    if time_since_last < current_delay:
        wait_time = current_delay - time_since_last
        
        # Add some randomness to appear more human-like
        jitter = random.uniform(-0.1, 0.1) * wait_time
        wait_time += jitter
        
        logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
        await asyncio.sleep(wait_time)
    
    # Update last request time
    last_request_time = time.time()
    
def increase_delay():
    """Increase delay after encountering rate limiting or errors."""
    global current_delay, consecutive_errors
    
    consecutive_errors += 1
    
    # Exponential backoff with maximum
    current_delay = min(current_delay * RATE_LIMIT_FACTOR, MAX_DELAY)
    
    logger.info(f"Increased rate limit delay to {current_delay:.2f}s after error")
    
def decrease_delay():
    """Gradually decrease delay after successful requests."""
    global current_delay, consecutive_errors
    
    consecutive_errors = 0
    
    # Gradually decrease delay, but not below initial delay
    if current_delay > INITIAL_DELAY:
        current_delay = max(current_delay / RATE_LIMIT_FACTOR, INITIAL_DELAY)
        logger.debug(f"Decreased rate limit delay to {current_delay:.2f}s after success")