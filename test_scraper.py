# test_scraper.py
import asyncio
from main import main

async def test():
    """Test the scraper with a known public Facebook post."""
    # Replace with a public Facebook post URL
    test_url = "https://www.facebook.com/photo/?fbid=1160696216103781&set=a.475298814643528"
    
    # Set up command line arguments
    import sys
    sys.argv = [
        "main.py",
        "--url", test_url,
        "--max-comments", "10",
        "--format", "json"
    ]
    
    # Run the main function
    await main()

if __name__ == "__main__":
    asyncio.run(test())