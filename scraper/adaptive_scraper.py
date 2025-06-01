# scraper/adaptive_scraper.py
import os
import json
import asyncio
import pandas as pd
from datetime import datetime
from utils.logger import get_logger
from config import MAX_COMMENTS_PER_POST, OUTPUT_DIR, OUTPUT_FORMAT

logger = get_logger(__name__)

class AdaptiveScraper:
    """Main scraper class that adapts to Facebook's changing structure."""
    
    def __init__(self, auth_manager, gemini_processor, data_fetcher, pattern_store, proxy_manager=None):
        """Initialize the adaptive scraper.
        
        Args:
            auth_manager: Authentication manager instance
            gemini_processor: Gemini API processor instance
            data_fetcher: Data fetcher instance
            pattern_store: Pattern store instance
            proxy_manager: Optional proxy manager instance
        """
        self.auth_manager = auth_manager
        self.gemini_processor = gemini_processor
        self.data_fetcher = data_fetcher
        self.pattern_store = pattern_store
        self.proxy_manager = proxy_manager
        
    async def scrape_comments(self, post_url, max_comments=MAX_COMMENTS_PER_POST):
        """Scrape comments from a Facebook post.
        
        Args:
            post_url (str): URL of the Facebook post
            max_comments (int): Maximum number of comments to scrape
            
        Returns:
            list: Extracted comments
        """
        logger.info(f"Scraping comments from {post_url}")
        
        # Try to fetch with requests first (faster)
        html_content = await self.data_fetcher.fetch_with_requests(post_url)
        
        # If requests fails, try with Playwright
        if not html_content:
            logger.info("Requests method failed, trying with Playwright")
            
            # Initialize browser session
            page = await self.auth_manager.initialize_session()
            
            # Fetch with Playwright
            html_content = await self.data_fetcher.fetch_with_playwright(
                post_url, 
                page=page, 
                scroll_for_comments=True
            )
            
            # Close session
            await self.auth_manager.close_session()
            
        # If we still don't have content, return empty list
        if not html_content:
            logger.error(f"Failed to fetch content from {post_url}")
            return []
            
        # Try existing patterns first for efficiency
        comments = await self._try_existing_patterns(html_content, post_url)
        
        # If patterns fail or return too few comments, use Gemini
        if not comments or len(comments) < max_comments:
            logger.info("Existing patterns insufficient, using Gemini for analysis")
            
            # Use Gemini to analyze the page structure
            comments = await self.gemini_processor.analyze_page_structure(html_content)
            
            # Store successful pattern for future use if we got results
            if comments:
                pattern_data = {
                    "extraction_method": "gemini",
                    "timestamp": datetime.now().isoformat(),
                    "sample_result": comments[:2] if len(comments) >= 2 else comments
                }
                self.pattern_store.add_pattern(post_url, pattern_data)
                
        # Limit to requested number of comments
        comments = comments[:max_comments]
        
        logger.info(f"Successfully scraped {len(comments)} comments from {post_url}")
        return comments
        
    async def _try_existing_patterns(self, html_content, url):
        """Try to extract using previously successful patterns.
        
        Args:
            html_content (str): HTML content to extract from
            url (str): URL being scraped
            
        Returns:
            list: Extracted comments or empty list if no patterns match
        """
        # Get matching patterns
        matching_patterns = self.pattern_store.get_matching_patterns(url)
        
        if not matching_patterns:
            logger.info("No matching patterns found")
            return []
            
        # Try each pattern in order of success rate
        for pattern in matching_patterns:
            pattern_id = pattern["id"]
            pattern_data = pattern["data"]
            
            logger.info(f"Trying pattern {pattern_id} (success rate: {pattern_data['success_rate']:.2f})")
            
            # For now, we only support Gemini extraction
            # Future versions could implement CSS/XPath based extraction
            if pattern_data["extraction_data"]["extraction_method"] == "gemini":
                # Use Gemini with the same approach
                comments = await self.gemini_processor.analyze_page_structure(html_content)
                
                # Check if we got results
                if comments:
                    logger.info(f"Pattern {pattern_id} successfully extracted {len(comments)} comments")
                    self.pattern_store.update_pattern_success(pattern_id)
                    return comments
                else:
                    logger.info(f"Pattern {pattern_id} failed to extract comments")
                    self.pattern_store.update_pattern_failure(pattern_id)
                    
        # If we get here, no patterns worked
        logger.info("All patterns failed, will try fresh analysis")
        return []
        
    async def scrape_multiple_posts(self, post_urls, max_comments_per_post=MAX_COMMENTS_PER_POST):
        """Scrape comments from multiple Facebook posts.
        
        Args:
            post_urls (list): List of Facebook post URLs
            max_comments_per_post (int): Maximum comments per post
            
        Returns:
            dict: Mapping of URLs to extracted comments
        """
        results = {}
        
        for url in post_urls:
            comments = await self.scrape_comments(url, max_comments_per_post)
            results[url] = comments
            
            # Small delay between posts to avoid triggering rate limits
            await asyncio.sleep(2)
            
        return results
        
    def save_comments(self, comments, output_file=None, format=OUTPUT_FORMAT):
        """Save extracted comments to a file.
        
        Args:
            comments: Comments to save (list or dict)
            output_file (str): Output file path
            format (str): Output format (csv or json)
            
        Returns:
            str: Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Generate default filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(OUTPUT_DIR, f"facebook_comments_{timestamp}.{format}")
            
        # Ensure output file has correct extension
        if not output_file.endswith(f".{format}"):
            output_file = f"{output_file}.{format}"
            
        # Convert comments to appropriate format and save
        if isinstance(comments, dict):
            # Multiple posts
            if format == "json":
                with open(output_file, 'w') as f:
                    json.dump(comments, f, indent=2)
            else:  # csv
                # Flatten the dictionary into a list of comments with post URL
                flat_comments = []
                for url, post_comments in comments.items():
                    for comment in post_comments:
                        comment_with_url = comment.copy()
                        comment_with_url["post_url"] = url
                        flat_comments.append(comment_with_url)
                        
                # Convert to DataFrame and save as CSV
                df = pd.DataFrame(flat_comments)
                df.to_csv(output_file, index=False)
        else:
            # Single post
            if format == "json":
                with open(output_file, 'w') as f:
                    json.dump(comments, f, indent=2)
            else:  # csv
                df = pd.DataFrame(comments)
                df.to_csv(output_file, index=False)
                
        logger.info(f"Saved comments to {output_file}")
        return output_file