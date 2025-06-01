# scraper/data_fetcher.py
import random
import time
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from utils.logger import get_logger
from utils.rate_limiter import adaptive_delay
from config import REQUEST_TIMEOUT

logger = get_logger(__name__)

class DataFetcher:
    """Handles fetching data from Facebook with anti-detection measures."""
    
    def __init__(self, auth_manager=None, proxy_manager=None):
        """Initialize the data fetcher.
        
        Args:
            auth_manager: Authentication manager instance
            proxy_manager: Proxy manager instance
        """
        self.auth_manager = auth_manager
        self.proxy_manager = proxy_manager
        
    async def fetch_with_requests(self, url):
        """Fetch page content using aiohttp with anti-bot evasion.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content
        """
        logger.info(f"Fetching {url} with aiohttp")
        
        # Get proxy if available
        proxy = self.proxy_manager.get_current_proxy() if self.proxy_manager else None
        
        # Prepare headers with random user agent
        headers = {
            "User-Agent": random.choice(self.auth_manager.USER_AGENTS) if self.auth_manager else "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
        # Add random referer sometimes
        if random.random() > 0.5:
            referers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.facebook.com/",
                "https://www.reddit.com/"
            ]
            headers["Referer"] = random.choice(referers)
        
        try:
            # Apply adaptive delay for rate limiting
            await adaptive_delay()
            
            # Create session with proxy if available
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    allow_redirects=True
                ) as response:
                    
                    # Check if we need to rotate proxy
                    if self.proxy_manager and response.status in [403, 429, 503]:
                        logger.warning(f"Received status {response.status}, rotating proxy")
                        self.proxy_manager.rotate_proxy()
                    
                    # Return content if successful
                    if response.status == 200:
                        html = await response.text()
                        logger.info(f"Successfully fetched {url}")
                        return html
                    else:
                        logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    async def fetch_with_playwright(self, url, page=None, scroll_for_comments=True):
        """Fetch page content using Playwright with full browser rendering.
        
        Args:
            url (str): URL to fetch
            page: Existing Playwright page object
            scroll_for_comments (bool): Whether to scroll to load more comments
            
        Returns:
            str: HTML content
        """
        logger.info(f"Fetching {url} with Playwright")
        
        # Create new page if not provided
        close_after = False
        if page is None:
            close_after = True
            async with async_playwright() as playwright:
                browser = await playwright.firefox.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=random.choice(self.auth_manager.USER_AGENTS) if self.auth_manager else None
                )
                page = await context.new_page()
        
        try:
            # Apply adaptive delay for rate limiting
            await adaptive_delay()
            
            # Navigate to the URL
            await page.goto(url, wait_until="networkidle")
            
            # Handle cookie consent if present
            cookie_buttons = [
                'button[data-cookiebanner="accept_button"]',
                'button[data-testid="cookie-policy-manage-dialog-accept-button"]',
                'button[title="Accept All"]',
                'button[title="Accept all"]'
            ]
            
            for selector in cookie_buttons:
                try:
                    if await page.query_selector(selector):
                        await page.click(selector)
                        logger.info("Accepted cookies")
                        await page.wait_for_timeout(1000)
                        break
                except:
                    continue
            
            # Scroll to load more comments if needed
            if scroll_for_comments:
                logger.info("Scrolling to load more comments")
                
                # Initial wait for page to stabilize
                await page.wait_for_timeout(2000)
                
                # Look for "View more comments" or "See more" buttons
                more_comments_selectors = [
                    'div[role="button"]:has-text("View more comments")',
                    'div[role="button"]:has-text("See more")',
                    'a:has-text("View more comments")',
                    'a:has-text("See more comments")',
                    'span:has-text("View more comments")'
                ]
                
                # Click "View more comments" buttons
                for _ in range(3):  # Try to load more comments 3 times
                    clicked = False
                    for selector in more_comments_selectors:
                        try:
                            more_buttons = await page.query_selector_all(selector)
                            if more_buttons:
                                for button in more_buttons:
                                    await button.click()
                                    clicked = True
                                    await page.wait_for_timeout(2000)
                        except:
                            continue
                    
                    if not clicked:
                        break
                
                # Scroll down a few times to reveal more content
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await page.wait_for_timeout(random.uniform(500, 1500))
            
            # Get the final HTML content
            html_content = await page.content()
            logger.info(f"Successfully fetched {url} with Playwright")
            
            # Close browser if we created it
            if close_after:
                await browser.close()
                
            return html_content
            
        except Exception as e:
            logger.error(f"Error fetching {url} with Playwright: {str(e)}")
            
            # Close browser if we created it
            if close_after:
                await browser.close()
                
            return None