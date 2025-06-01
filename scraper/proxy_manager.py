# scraper/proxy_manager.py
import random
from utils.logger import get_logger
from config import PROXY_ROTATION_FREQUENCY

logger = get_logger(__name__)

class ProxyManager:
    """Manages proxy rotation for avoiding IP-based rate limits and bans."""
    
    def __init__(self, proxy_list=None, rotation_frequency=PROXY_ROTATION_FREQUENCY):
        """Initialize the proxy manager.
        
        Args:
            proxy_list (list): List of proxy URLs
            rotation_frequency (int): How often to rotate proxies
        """
        self.proxy_list = proxy_list or []
        self.rotation_frequency = rotation_frequency
        self.current_proxy_index = 0
        self.request_count = 0
        
        if not self.proxy_list:
            logger.warning("No proxies provided to proxy manager")
            
    def add_proxies(self, proxies):
        """Add proxies to the proxy list.
        
        Args:
            proxies (list): List of proxy URLs to add
        """
        self.proxy_list.extend(proxies)
        logger.info(f"Added {len(proxies)} proxies, total now {len(self.proxy_list)}")
        
    def get_current_proxy(self):
        """Get the current proxy configuration.
        
        Returns:
            str: Proxy URL or None if no proxies available
        """
        if not self.proxy_list:
            return None
            
        return self.proxy_list[self.current_proxy_index]
        
    def rotate_proxy(self):
        """Rotate to the next proxy in the list.
        
        Returns:
            str: New proxy URL or None if no proxies available
        """
        if not self.proxy_list:
            return None
            
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        self.request_count = 0
        
        logger.info(f"Rotated to proxy {self.current_proxy_index + 1}/{len(self.proxy_list)}")
        return self.get_current_proxy()
        
    def should_rotate(self):
        """Determine if proxy rotation is needed.
        
        Returns:
            bool: Whether proxy should be rotated
        """
        self.request_count += 1
        
        if self.request_count >= self.rotation_frequency:
            logger.info(f"Reached {self.request_count} requests with current proxy, should rotate")
            return True
            
        return False
        
    def get_random_proxy(self):
        """Get a random proxy from the list.
        
        Returns:
            str: Random proxy URL or None if no proxies available
        """
        if not self.proxy_list:
            return None
            
        return random.choice(self.proxy_list)