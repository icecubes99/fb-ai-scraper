# scraper/gemini_processor.py
import json
import asyncio
import google.generativeai as genai
from bs4 import BeautifulSoup
import markdown
from utils.logger import get_logger
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = get_logger(__name__)

class GeminiProcessor:
    """Handles integration with Google's Gemini API for content analysis."""
    
    def __init__(self, api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL):
        """Initialize the Gemini processor.
        
        Args:
            api_key (str): Gemini API key
            model_name (str): Gemini model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.genai = self._initialize_gemini()
        self.model = self._get_model()
        
    def _initialize_gemini(self):
        """Initialize the Gemini API client.
        
        Returns:
            Initialized Gemini client
        """
        if not self.api_key:
            raise ValueError("Gemini API key is required")
            
        genai.configure(api_key=self.api_key)
        return genai
        
    def _get_model(self):
        """Get the specified Gemini model.
        
        Returns:
            Gemini model instance
        """
        return self.genai.GenerativeModel(self.model_name)
        
    def _html_to_markdown(self, html):
        """Convert HTML to markdown for better Gemini processing.
        
        Args:
            html (str): HTML content
            
        Returns:
            str: Markdown representation of the HTML
        """
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Extract text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Find all comment-like structures for additional context
        potential_comments = []
        
        # Look for common comment container patterns
        comment_containers = soup.select('div[role="article"], div.comment, div._4eek, div.UFICommentContent')
        for container in comment_containers:
            potential_comments.append(container.get_text(separator=' ', strip=True))
            
        # Add potential comments as context
        if potential_comments:
            text += "\n\nPotential Comments Found:\n" + "\n".join(potential_comments)
            
        return text
        
    async def analyze_page_structure(self, html_content):
        """Analyze Facebook page structure to identify comment patterns.
        
        Args:
            html_content (str): Raw HTML content of the Facebook page
            
        Returns:
            list: Extracted comments
        """
        logger.info("Analyzing page structure with Gemini")
        
        # Convert HTML to a format Gemini can process effectively
        markdown_content = self._html_to_markdown(html_content)
        
        # Truncate if too long (Gemini has token limits)
        if len(markdown_content) > 30000:
            markdown_content = markdown_content[:30000]
            logger.warning("Content truncated to 30,000 characters due to model limits")
        
        # Prompt Gemini to identify comment patterns
        prompt = f"""
        Analyze this Facebook page content and identify all comment containers.
        For each comment, extract:
        1. The comment text only (no names or personal identifiers)
        2. Any relevant metadata (timestamp, etc.)
        
        Return the results as a JSON array of comment objects with these fields:
        - comment_text: The text content of the comment
        - timestamp: The timestamp of the comment (if available)
        
        Important guidelines:
        - Focus ONLY on comments, not the original post
        - Exclude all personal identifying information
        - If you can't find any comments, return an empty array
        
        Content:
        {markdown_content}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return self._parse_gemini_response(response)
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return []
        
    def _parse_gemini_response(self, response):
        """Extract structured data from Gemini's response.
        
        Args:
            response: Gemini API response
            
        Returns:
            list: Extracted comments
        """
        try:
            # Extract text from response
            response_text = response.text
            
            # Look for JSON array in the response
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                comments = json.loads(json_str)
                logger.info(f"Successfully extracted {len(comments)} comments")
                return comments
            else:
                # Try to find any JSON-like structure
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    json_str = response_text[start_idx:end_idx+1]
                    try:
                        comments = json.loads(json_str)
                        logger.info(f"Successfully extracted {len(comments)} comments using fallback method")
                        return comments
                    except json.JSONDecodeError:
                        pass
                
                logger.warning("Could not extract structured data from Gemini response")
                return []
                
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return []
            
    async def learn_from_changes(self, old_pattern, new_html, success_rate):
        """Use Gemini to analyze changes in Facebook's structure.
        
        Args:
            old_pattern (dict): Previously successful pattern
            new_html (str): New HTML that doesn't match the pattern
            success_rate (float): Success rate of the old pattern
            
        Returns:
            dict: Updated pattern information
        """
        logger.info("Learning from Facebook structure changes")
        
        # Convert HTML to a format Gemini can process effectively
        markdown_content = self._html_to_markdown(new_html)
        
        # Truncate if too long
        if len(markdown_content) > 20000:
            markdown_content = markdown_content[:20000]
        
        # Prompt Gemini to analyze the changes
        prompt = f"""
        I'm trying to extract comments from Facebook posts, but the HTML structure has changed.

        Previous working pattern:
        {json.dumps(old_pattern, indent=2)}

        New HTML structure (sample):
        {markdown_content[:5000]}  # First 5000 chars for context

        Please:
        1. Analyze how the comment structure has changed
        2. Provide a new extraction pattern that would work with this updated structure
        3. Explain the key differences between old and new patterns

        Return your response as a JSON object with:
        - analysis: your explanation of the changes
        - new_pattern: the updated extraction pattern
        - selector_strategy: recommended approach (CSS, XPath, or regex)
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            
            # Parse the response to extract the new pattern
            response_text = response.text
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{\s*"analysis".*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                pattern_info = json.loads(json_str)
                logger.info("Successfully learned new pattern from structure changes")
                return pattern_info
            else:
                logger.warning("Could not extract structured pattern data from Gemini response")
                return {
                    "analysis": "Failed to analyze changes",
                    "new_pattern": old_pattern,
                    "selector_strategy": "fallback"
                }
                
        except Exception as e:
            logger.error(f"Error learning from changes: {str(e)}")
            return {
                "analysis": f"Error: {str(e)}",
                "new_pattern": old_pattern,
                "selector_strategy": "fallback"
            }