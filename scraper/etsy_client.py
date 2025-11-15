"""
Etsy HTTP Client
Handles HTTP requests with rate limiting, retry logic, and user-agent rotation
"""

import requests
import time
import random
import logging
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class EtsyClient:
    """HTTP client for Etsy with rate limiting and error handling"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    def __init__(self, delay: float = 2.0, max_retries: int = 3, timeout: int = 30):
        """
        Initialize Etsy client

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

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return random.choice(self.USER_AGENTS)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a GET request with rate limiting and error handling

        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests.get()

        Returns:
            Response object or None if request failed
        """
        self._rate_limit()

        # Set random user agent if not provided
        headers = kwargs.pop('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self._get_random_user_agent()

        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error fetching {url}: {e}")
            return None

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout fetching {url}: {e}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
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
