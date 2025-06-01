# scraper/auth_manager.py
import random
import asyncio
from playwright.async_api import async_playwright
from utils.logger import get_logger

logger = get_logger(__name__)

class AuthManager:
    """Manages authentication and session handling for Facebook access."""
    
    # List of common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    
    def __init__(self, use_cookies=True, headless=True, user_agent_rotation=True):
        """Initialize the authentication manager.
        
        Args:
            use_cookies (bool): Whether to use cookies for authentication
            headless (bool): Whether to run the browser in headless mode
            user_agent_rotation (bool): Whether to rotate user agents
        """
        self.use_cookies = use_cookies
        self.headless = headless
        self.user_agent_rotation = user_agent_rotation
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize_session(self):
        """Initialize a browser session with anti-fingerprinting measures.
        
        Returns:
            A browser page object with an established session
        """
        logger.info("Initializing browser session")
        
        self.playwright = await async_playwright().start()
        
        # Select a random user agent if rotation is enabled
        user_agent = random.choice(self.USER_AGENTS) if self.user_agent_rotation else None
        
        # Launch browser with appropriate settings
        self.browser = await self.playwright.firefox.launch(headless=self.headless)
        
        # Create a context with modified fingerprint
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "device_scale_factor": 1,
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }
        
        if user_agent:
            context_options["user_agent"] = user_agent
            
        self.context = await self.browser.new_context(**context_options)
        
        # Add additional fingerprint evasion
        await self.context.add_init_script("""
        // Modify navigator properties to avoid fingerprinting
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Modify canvas fingerprinting
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, width, height) {
            const imageData = originalGetImageData.call(this, x, y, width, height);
            const data = imageData.data;
            
            // Add slight noise to canvas data to prevent fingerprinting
            for (let i = 0; i < data.length; i += 4) {
                data[i] = data[i] + Math.floor(Math.random() * 2);
                data[i+1] = data[i+1] + Math.floor(Math.random() * 2);
                data[i+2] = data[i+2] + Math.floor(Math.random() * 2);
            }
            
            return imageData;
        };
        """)
        
        # Create a new page
        self.page = await self.context.new_page()
        
        # Add random delays to page interactions to mimic human behavior
        self.page.set_default_timeout(30000)  # 30 seconds
        
        logger.info("Browser session initialized successfully")
        return self.page
    
    async def close_session(self):
        """Close the browser session."""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            logger.info("Browser session closed")
    
    async def handle_login(self, email=None, password=None):
        """Handle Facebook login if credentials are provided.
        
        Args:
            email (str): Facebook email/username
            password (str): Facebook password
            
        Returns:
            bool: Whether login was successful
        """
        if not email or not password:
            logger.info("No credentials provided, skipping login")
            return False
            
        if not self.page:
            logger.error("No active browser session")
            return False
            
        try:
            # Navigate to Facebook login page
            await self.page.goto("https://www.facebook.com/")
            
            # Check for and handle cookie consent dialog
            if await self.page.query_selector('button[data-cookiebanner="accept_button"]'):
                await self.page.click('button[data-cookiebanner="accept_button"]')
                logger.info("Accepted cookies")
                
            # Fill in login form
            await self.page.fill('input[name="email"]', email)
            await self.page.fill('input[name="pass"]', password)
            
            # Add a small delay to mimic human behavior
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Click login button
            await self.page.click('button[name="login"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if "login" in self.page.url or "checkpoint" in self.page.url:
                logger.error("Login failed or additional verification required")
                return False
                
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False