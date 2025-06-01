# Facebook AI Scraper

An intelligent Facebook comment scraper that combines AI-powered content analysis with adaptive pattern matching to extract comments from public Facebook posts.

## Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini API to intelligently identify comment structures
- 🔄 **Adaptive Pattern Matching**: Learns and adapts to Facebook's changing HTML structure
- 🎭 **Anti-Detection**: Browser fingerprint evasion and human-like behavior simulation
- 📱 **Multiple Fetch Methods**: Falls back from HTTP requests to browser automation
- 💾 **Flexible Output**: Supports JSON and CSV export formats
- 🔍 **Smart Retry Logic**: Handles rate limits and temporary failures gracefully
- 📊 **Progress Tracking**: Real-time progress monitoring with detailed logging

## Prerequisites

- Python 3.8+
- Google Gemini API key (free tier available)
- Virtual environment (recommended)

## Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd fb-ai-scraper
   ```

2. **Create and activate virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

## Configuration

1. **Get a Gemini API Key**

   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Note: Free tier has daily/minute limits

2. **Set up environment variables**
   Create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-1.5-pro
   ```

3. **Configure settings** (optional)
   Edit `config.py` to customize:
   - API endpoints
   - Rate limiting
   - Output formats
   - Browser settings

## Usage

### Basic Usage

```bash
python main.py --url "https://www.facebook.com/page/posts/123456" --max-comments 50
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --url TEXT              Facebook post URL (required)
  --max-comments INTEGER  Maximum comments to scrape (default: 100)
  --format [json|csv]     Output format (default: json)
  --output TEXT           Output file path (optional)
  --headless              Run browser in headless mode
  --help                  Show this message and exit
```

### Examples

**Scrape 20 comments in JSON format:**

```bash
python main.py --url "https://www.facebook.com/post/123" --max-comments 20 --format json
```

**Scrape with visible browser (for debugging):**

```bash
python main.py --url "https://www.facebook.com/post/123" --max-comments 10 --no-headless
```

**Export to specific file:**

```bash
python main.py --url "https://www.facebook.com/post/123" --output my_comments.csv --format csv
```

### Programmatic Usage

```python
import asyncio
from scraper.adaptive_scraper import AdaptiveScraper

async def scrape_comments():
    scraper = AdaptiveScraper()
    comments = await scraper.scrape_comments(
        url="https://www.facebook.com/post/123",
        max_comments=50
    )
    return comments

# Run the scraper
comments = asyncio.run(scrape_comments())
```

## Project Structure

```
fb-ai-scraper/
├── scraper/
│   ├── adaptive_scraper.py    # Main scraping logic
│   ├── auth_manager.py        # Browser session management
│   ├── data_fetcher.py        # HTTP/Playwright data fetching
│   ├── gemini_processor.py    # AI-powered content analysis
│   └── pattern_store.py       # Pattern learning and storage
├── utils/
│   └── logger.py              # Logging configuration
├── data/
│   ├── output/                # Scraped data output
│   └── patterns/              # Learned extraction patterns
├── config.py                  # Configuration settings
├── main.py                    # CLI entry point
├── test_scraper.py           # Test script
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## How It Works

1. **Initial Attempt**: Tries to fetch content via HTTP requests (fastest)
2. **Browser Fallback**: If HTTP fails, launches Playwright browser
3. **Pattern Matching**: Searches for known comment extraction patterns
4. **AI Analysis**: If no patterns match, uses Gemini AI to analyze the page structure
5. **Adaptive Learning**: Stores successful patterns for future use
6. **Data Export**: Saves comments in requested format

## API Quotas & Limitations

### Gemini API Free Tier Limits

- **Requests per minute**: 15
- **Requests per day**: 1,500
- **Input tokens per minute**: 32,000

### Handling Quota Limits

- The scraper automatically retries after quota reset
- Consider upgrading to paid tier for heavy usage
- Optimize by reducing HTML content size sent to AI

### Facebook Rate Limiting

- Uses randomized delays between requests
- Rotates user agents to avoid detection
- Implements browser fingerprint evasion

## Troubleshooting

### Common Issues

**Import errors:**

```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Playwright browser not found:**

```bash
playwright install
```

**Gemini API quota exceeded:**

- Wait for quota reset (typically 1 minute)
- Check your API usage at [Google AI Studio](https://aistudio.google.com/)
- Consider upgrading your plan

**No comments found:**

- Facebook may have changed their HTML structure
- The AI will learn new patterns over time
- Check if the post has public comments

**Browser detection:**

- Facebook may detect automated browsing
- Try running with `--no-headless` to debug
- Consider adding longer delays between requests

### Debug Mode

Run with visible browser to see what's happening:

```bash
python main.py --url "your-url" --no-headless
```

Enable verbose logging by editing `utils/logger.py` to set level to `DEBUG`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This tool is for educational and research purposes only. Always respect:

- Facebook's Terms of Service
- Website robots.txt files
- Rate limiting and fair usage
- Privacy and data protection laws
- Public vs private content boundaries

## License

MIT License - see LICENSE file for details.

## Support

- Check existing GitHub issues
- Create a new issue with detailed error logs
- Include your Python version and OS information
