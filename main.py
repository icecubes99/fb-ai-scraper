# main.py
import os
import asyncio
import argparse
from dotenv import load_dotenv
from scraper.auth_manager import AuthManager
from scraper.data_fetcher import DataFetcher
from scraper.gemini_processor import GeminiProcessor
from scraper.pattern_store import PatternStore
from scraper.proxy_manager import ProxyManager
from scraper.adaptive_scraper import AdaptiveScraper
from utils.logger import get_logger
from config import USE_PROXIES, HEADLESS_BROWSER, USER_AGENT_ROTATION

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

async def main():
    """Main entry point for the Facebook comments scraper."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI-Assisted Facebook Comments Scraper")
    parser.add_argument("--url", type=str, help="Facebook post URL to scrape")
    parser.add_argument("--urls-file", type=str, help="File containing Facebook post URLs (one per line)")
    parser.add_argument("--max-comments", type=int, default=100, help="Maximum comments to scrape per post")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument("--proxy-list", type=str, help="File containing proxy URLs (one per line)")
    args = parser.parse_args()
    
    # Validate arguments
    if not args.url and not args.urls_file:
        parser.error("Either --url or --urls-file must be provided")
        
    # Initialize components
    logger.info("Initializing scraper components")
    
    # Set up proxy manager if needed
    proxy_manager = None
    if USE_PROXIES or args.proxy_list:
        proxy_manager = ProxyManager()
        
        if args.proxy_list and os.path.exists(args.proxy_list):
            with open(args.proxy_list, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
                proxy_manager.add_proxies(proxies)
    
    # Initialize other components
    auth_manager = AuthManager(
        use_cookies=True,
        headless=HEADLESS_BROWSER,
        user_agent_rotation=USER_AGENT_ROTATION
    )
    
    gemini_processor = GeminiProcessor()
    
    data_fetcher = DataFetcher(
        auth_manager=auth_manager,
        proxy_manager=proxy_manager
    )
    
    pattern_store = PatternStore()
    
    # Initialize the adaptive scraper
    scraper = AdaptiveScraper(
        auth_manager=auth_manager,
        gemini_processor=gemini_processor,
        data_fetcher=data_fetcher,
        pattern_store=pattern_store,
        proxy_manager=proxy_manager
    )
    
    # Get URLs to scrape
    urls_to_scrape = []
    
    if args.url:
        urls_to_scrape.append(args.url)
        
    if args.urls_file and os.path.exists(args.urls_file):
        with open(args.urls_file, 'r') as f:
            file_urls = [line.strip() for line in f if line.strip()]
            urls_to_scrape.extend(file_urls)
    
    # Scrape comments
    if len(urls_to_scrape) == 1:
        # Single URL
        logger.info(f"Scraping comments from {urls_to_scrape[0]}")
        comments = await scraper.scrape_comments(urls_to_scrape[0], args.max_comments)
        
        # Save results
        output_file = scraper.save_comments(comments, args.output, args.format)
        logger.info(f"Scraped {len(comments)} comments, saved to {output_file}")
        
    else:
        # Multiple URLs
        logger.info(f"Scraping comments from {len(urls_to_scrape)} URLs")
        results = await scraper.scrape_multiple_posts(urls_to_scrape, args.max_comments)
        
        # Count total comments
        total_comments = sum(len(comments) for comments in results.values())
        
        # Save results
        output_file = scraper.save_comments(results, args.output, args.format)
        logger.info(f"Scraped {total_comments} comments from {len(urls_to_scrape)} posts, saved to {output_file}")
    
    logger.info("Scraping completed successfully")

if __name__ == "__main__":
    asyncio.run(main())