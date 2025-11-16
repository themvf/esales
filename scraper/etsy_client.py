"""
Etsy HTTP Client
Handles HTTP requests using Firecrawl API or cloudscraper fallback
"""

import os
import time
import logging
from typing import Optional

try:
    from firecrawl import Firecrawl
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    import requests

logger = logging.getLogger(__name__)


class EtsyClient:
    """HTTP client for Etsy with Firecrawl API (bypasses all anti-bot protection)"""

    def __init__(self, delay: float = 2.0, max_retries: int = 3, timeout: int = 30, firecrawl_api_key: str = None):
        """
        Initialize Etsy client with Firecrawl API or cloudscraper fallback

        Args:
            delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            firecrawl_api_key: Firecrawl API key (or set FIRECRAWL_API_KEY env var)
        """
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request_time = 0

        # Try to get Firecrawl API key
        self.firecrawl_api_key = firecrawl_api_key or os.getenv('FIRECRAWL_API_KEY')

        # Initialize Firecrawl if available and configured
        if FIRECRAWL_AVAILABLE and self.firecrawl_api_key:
            try:
                self.firecrawl = Firecrawl(api_key=self.firecrawl_api_key)
                self.use_firecrawl = True
                logger.info("✅ Firecrawl initialized - using API for scraping")
            except Exception as e:
                logger.warning(f"Failed to initialize Firecrawl: {e}. Falling back to cloudscraper")
                self.use_firecrawl = False
                self.session = self._create_session()
        else:
            if not FIRECRAWL_AVAILABLE:
                logger.warning("Firecrawl not installed. Install with: pip install firecrawl-py")
            elif not self.firecrawl_api_key:
                logger.warning("No Firecrawl API key found. Set FIRECRAWL_API_KEY environment variable")
            logger.info("Using cloudscraper fallback")
            self.use_firecrawl = False
            self.session = self._create_session()

    def _create_session(self):
        """Create a cloudscraper session with enhanced anti-detection"""
        if CLOUDSCRAPER_AVAILABLE:
            # Create scraper with enhanced browser fingerprinting
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False,
                    'desktop': True
                },
                delay=15,
                debug=False,
                interpreter='native'
            )

            # Add realistic browser headers
            scraper.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/'
            })
            return scraper
        else:
            # Fallback to plain requests
            return requests.Session()

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> Optional:
        """
        Make a GET request using Firecrawl or cloudscraper fallback

        Args:
            url: URL to fetch
            **kwargs: Additional arguments

        Returns:
            Response-like object with .text and .status_code attributes, or None if failed
        """
        self._rate_limit()

        if self.use_firecrawl:
            return self._get_with_firecrawl(url)
        else:
            return self._get_with_cloudscraper(url, **kwargs)

    def _get_with_firecrawl(self, url: str):
        """Fetch URL using Firecrawl API"""
        try:
            logger.debug(f"Fetching with Firecrawl: {url}")

            # Use Firecrawl's scrape method with correct signature
            result = self.firecrawl.scrape(
                url,
                formats=["html", "markdown"],
                only_main_content=False  # Get full page
            )

            # Result structure: result has 'html', 'markdown', etc.
            if result and 'html' in result:
                # Create a response-like object
                class FirecrawlResponse:
                    def __init__(self, html_content, url):
                        self.text = html_content
                        self.content = html_content.encode('utf-8')
                        self.status_code = 200
                        self.url = url

                    def raise_for_status(self):
                        pass

                response = FirecrawlResponse(result['html'], url)
                logger.info(f"✅ Successfully fetched with Firecrawl: {url}")
                return response
            else:
                logger.error(f"Firecrawl returned no HTML for {url}")
                return None

        except Exception as e:
            logger.error(f"Firecrawl error for {url}: {e}")
            # Try fallback to cloudscraper if Firecrawl fails
            logger.info("Attempting cloudscraper fallback...")
            if not hasattr(self, 'session'):
                self.session = self._create_session()
            return self._get_with_cloudscraper(url)

    def _get_with_cloudscraper(self, url: str, **kwargs):
        """Fetch URL using cloudscraper"""
        try:
            logger.debug(f"Fetching with cloudscraper: {url}")

            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout

            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            logger.info(f"✅ Successfully fetched with cloudscraper: {url}")
            return response

        except Exception as e:
            logger.error(f"Cloudscraper error for {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
            return None

    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
