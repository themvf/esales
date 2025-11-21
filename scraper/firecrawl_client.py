"""
Firecrawl Client
Handles interactions with the Firecrawl API for scraping
"""

import logging
import os
from typing import Optional, Dict, Any
from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)

class FirecrawlClient:
    """Client for Firecrawl API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl client
        
        Args:
            api_key: Firecrawl API key. If None, tries to get from env var FIRECRAWL_API_KEY
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            logger.warning("No Firecrawl API key provided. Scraper will fail if Firecrawl is required.")
        
        try:
            self.app = FirecrawlApp(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize FirecrawlApp: {e}")
            self.app = None

    def get(self, url: str) -> Optional[Any]:
        """
        Scrape a URL using Firecrawl
        
        Args:
            url: URL to scrape
            
        Returns:
            Mock response object with .text attribute containing HTML, or None if failed
        """
        if not self.app:
            logger.error("FirecrawlApp not initialized")
            return None

        try:
            logger.info(f"Scraping with Firecrawl: {url}")
            # Use scrape_url to get the content
            # We want the raw HTML to pass to our existing extractors
            result = self.app.scrape_url(url, params={'formats': ['html']})
            
            if result and 'html' in result:
                # Create a simple mock response object to match requests interface
                class MockResponse:
                    def __init__(self, text):
                        self.text = text
                        self.status_code = 200
                
                return MockResponse(result['html'])
            else:
                logger.error(f"Firecrawl returned no HTML for {url}")
                return None

        except Exception as e:
            logger.error(f"Error scraping {url} with Firecrawl: {e}")
            return None

    def close(self):
        """Cleanup resources (nothing to do for Firecrawl API)"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
