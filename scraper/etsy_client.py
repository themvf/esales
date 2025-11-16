"""
Etsy HTTP Client
Handles HTTP requests with Cloudflare bypass, rate limiting, and anti-detection
"""

import cloudscraper
import time
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EtsyClient:
    """HTTP client for Etsy with Cloudflare bypass and rate limiting"""

    def __init__(self, delay: float = 2.0, max_retries: int = 3, timeout: int = 30):
        """
        Initialize Etsy client with cloudscraper for Cloudflare bypass

        Args:
            delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request_time = 0
        self.session = self._create_session()

    def _create_session(self):
        """Create a cloudscraper session with enhanced anti-detection"""
        # Create scraper with enhanced browser fingerprinting
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False,
                'desktop': True
            },
            delay=15,  # Increased delay for challenge solving
            debug=False,
            # Use interpreter='nodejs' if available for better JS challenge solving
            interpreter='native'
        )

        # Add realistic browser headers
        scraper.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
            # Referer helps - makes it look like organic traffic
            'Referer': 'https://www.google.com/'
        })

        return scraper

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
        Make a GET request with Cloudflare bypass and rate limiting

        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to session.get()

        Returns:
            Response object or None if request failed
        """
        self._rate_limit()

        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching: {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, **kwargs)

                # Check if we got blocked
                if response.status_code == 403:
                    logger.warning(f"Got 403 on attempt {attempt + 1}, retrying...")
                    if attempt < self.max_retries - 1:
                        time.sleep((attempt + 1) * 5)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Failed after {self.max_retries} attempts with 403")
                        return None

                response.raise_for_status()
                logger.debug(f"Successfully fetched {url} ({len(response.content)} bytes)")
                return response

            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)  # Backoff
                else:
                    logger.error(f"Failed after {self.max_retries} attempts")
                    return None

        return None

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
