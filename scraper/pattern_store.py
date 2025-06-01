# scraper/pattern_store.py
import os
import json
import time
from utils.logger import get_logger
from config import PATTERN_STORAGE_PATH

logger = get_logger(__name__)

class PatternStore:
    """Stores and retrieves extraction patterns for Facebook comments."""
    
    def __init__(self, storage_path=PATTERN_STORAGE_PATH):
        """Initialize the pattern store.
        
        Args:
            storage_path (str): Path to the pattern storage file
        """
        self.storage_path = storage_path
        self.patterns = self._load_patterns()
        
    def _load_patterns(self):
        """Load previously successful patterns from storage.
        
        Returns:
            dict: Loaded patterns
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Try to load existing patterns
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded {len(patterns)} patterns from {self.storage_path}")
                return patterns
            except Exception as e:
                logger.error(f"Error loading patterns: {str(e)}")
                return {}
        else:
            logger.info(f"No pattern file found at {self.storage_path}, starting with empty patterns")
            return {}
            
    def _save_patterns(self):
        """Save patterns to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.patterns, f, indent=2)
            logger.info(f"Saved {len(self.patterns)} patterns to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving patterns: {str(e)}")
            
    def add_pattern(self, url_pattern, extraction_result):
        """Store a successful pattern for future use.
        
        Args:
            url_pattern (str): URL pattern this extraction works for
            extraction_result (dict): Extraction pattern and metadata
        """
        # Generate a pattern ID based on URL pattern
        pattern_id = f"pattern_{len(self.patterns) + 1}"
        
        # Store the pattern with metadata
        self.patterns[pattern_id] = {
            "url_pattern": url_pattern,
            "extraction_data": extraction_result,
            "created_at": time.time(),
            "last_used": time.time(),
            "success_count": 1,
            "failure_count": 0,
            "success_rate": 1.0
        }
        
        # Save updated patterns
        self._save_patterns()
        logger.info(f"Added new pattern {pattern_id} for URL pattern {url_pattern}")
        
    def get_matching_patterns(self, url):
        """Find patterns that might work for the given URL.
        
        Args:
            url (str): URL to match patterns against
            
        Returns:
            list: Matching patterns sorted by success rate
        """
        matching_patterns = []
        
        for pattern_id, pattern_data in self.patterns.items():
            # Simple substring matching for now
            # Could be enhanced with regex or more sophisticated matching
            if pattern_data["url_pattern"] in url or url in pattern_data["url_pattern"]:
                matching_patterns.append({
                    "id": pattern_id,
                    "data": pattern_data
                })
                
        # Sort by success rate (descending)
        matching_patterns.sort(key=lambda p: p["data"]["success_rate"], reverse=True)
        
        logger.info(f"Found {len(matching_patterns)} matching patterns for {url}")
        return matching_patterns
        
    def update_pattern_success(self, pattern_id):
        """Update pattern success statistics.
        
        Args:
            pattern_id (str): ID of the pattern to update
        """
        if pattern_id in self.patterns:
            self.patterns[pattern_id]["success_count"] += 1
            self.patterns[pattern_id]["last_used"] = time.time()
            
            # Recalculate success rate
            total = self.patterns[pattern_id]["success_count"] + self.patterns[pattern_id]["failure_count"]
            self.patterns[pattern_id]["success_rate"] = self.patterns[pattern_id]["success_count"] / total
            
            # Save updated patterns
            self._save_patterns()
            logger.info(f"Updated pattern {pattern_id} success stats")
            
    def update_pattern_failure(self, pattern_id):
        """Update pattern failure statistics.
        
        Args:
            pattern_id (str): ID of the pattern to update
        """
        if pattern_id in self.patterns:
            self.patterns[pattern_id]["failure_count"] += 1
            self.patterns[pattern_id]["last_used"] = time.time()
            
            # Recalculate success rate
            total = self.patterns[pattern_id]["success_count"] + self.patterns[pattern_id]["failure_count"]
            self.patterns[pattern_id]["success_rate"] = self.patterns[pattern_id]["success_count"] / total
            
            # Save updated patterns
            self._save_patterns()
            logger.info(f"Updated pattern {pattern_id} failure stats")