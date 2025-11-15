"""
Core Scraper
Main scraper class that orchestrates data collection
"""

import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .etsy_client import EtsyClient
from .extractors import (
    extract_listing_ids,
    extract_shop_info,
    extract_listing_info,
    extract_shop_url_from_listing
)

logger = logging.getLogger(__name__)


class EtsyScraper:
    """Main Etsy scraper class"""

    def __init__(self, delay: float = 2.0, max_workers: int = 5):
        """
        Initialize scraper

        Args:
            delay: Delay between requests in seconds
            max_workers: Maximum number of concurrent workers
        """
        self.client = EtsyClient(delay=delay)
        self.max_workers = max_workers
        self.base_url = "https://www.etsy.com"

    def scrape_page(self, url: str) -> List[str]:
        """
        Scrape a page and return listing IDs

        Args:
            url: URL of the page to scrape

        Returns:
            List of listing IDs found on the page
        """
        logger.info(f"Scraping page: {url}")
        response = self.client.get(url)

        if not response:
            logger.error(f"Failed to fetch page: {url}")
            return []

        listing_ids = extract_listing_ids(response.text)
        return listing_ids

    def scrape_listing(self, listing_id: str) -> Optional[Dict]:
        """
        Scrape a single listing

        Args:
            listing_id: ID of the listing to scrape

        Returns:
            Dictionary with listing information or None if failed
        """
        url = f"{self.base_url}/listing/{listing_id}"
        logger.info(f"Scraping listing: {listing_id}")

        response = self.client.get(url)
        if not response:
            logger.error(f"Failed to fetch listing: {listing_id}")
            return None

        listing_info = extract_listing_info(response.text, listing_id)
        listing_info['listing_url'] = url

        return listing_info

    def scrape_listings_batch(self, listing_ids: List[str]) -> List[Dict]:
        """
        Scrape multiple listings in parallel

        Args:
            listing_ids: List of listing IDs to scrape

        Returns:
            List of listing information dictionaries
        """
        logger.info(f"Scraping {len(listing_ids)} listings in batch")
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id = {
                executor.submit(self.scrape_listing, lid): lid
                for lid in listing_ids
            }

            for future in as_completed(future_to_id):
                listing_id = future_to_id[future]
                try:
                    listing_info = future.result()
                    if listing_info:
                        results.append(listing_info)
                except Exception as e:
                    logger.error(f"Error scraping listing {listing_id}: {e}")

        logger.info(f"Successfully scraped {len(results)}/{len(listing_ids)} listings")
        return results

    def scrape_shop(self, shop_name: str) -> Optional[Dict]:
        """
        Scrape shop information

        Args:
            shop_name: Name of the shop

        Returns:
            Dictionary with shop information or None if failed
        """
        url = f"{self.base_url}/shop/{shop_name}"
        logger.info(f"Scraping shop: {shop_name}")

        response = self.client.get(url)
        if not response:
            logger.error(f"Failed to fetch shop: {shop_name}")
            return None

        shop_info = extract_shop_info(response.text, shop_name)
        shop_info['shop_url'] = url

        return shop_info

    def scrape_shop_listings(self, shop_name: str, max_listings: int = None) -> List[Dict]:
        """
        Scrape all listings from a shop

        Args:
            shop_name: Name of the shop
            max_listings: Maximum number of listings to scrape (None for all)

        Returns:
            List of listing information dictionaries
        """
        logger.info(f"Scraping listings for shop: {shop_name}")

        # First get the shop page to find listings
        shop_url = f"{self.base_url}/shop/{shop_name}"
        response = self.client.get(shop_url)

        if not response:
            logger.error(f"Failed to fetch shop page: {shop_name}")
            return []

        # Extract listing IDs from shop page
        listing_ids = extract_listing_ids(response.text)

        if max_listings:
            listing_ids = listing_ids[:max_listings]

        logger.info(f"Found {len(listing_ids)} listings for shop {shop_name}")

        # Scrape all listings
        return self.scrape_listings_batch(listing_ids)

    def scrape_category(self, category_url: str, max_pages: int = 1) -> List[Dict]:
        """
        Scrape listings from a category page

        Args:
            category_url: URL of the category page
            max_pages: Maximum number of pages to scrape

        Returns:
            List of listing information dictionaries
        """
        logger.info(f"Scraping category: {category_url} (max {max_pages} pages)")

        all_listing_ids = []

        # Scrape multiple pages
        for page in range(1, max_pages + 1):
            # Add pagination parameter
            if '?' in category_url:
                page_url = f"{category_url}&page={page}"
            else:
                page_url = f"{category_url}?page={page}"

            listing_ids = self.scrape_page(page_url)
            all_listing_ids.extend(listing_ids)

            logger.info(f"Page {page}: Found {len(listing_ids)} listings")

            if not listing_ids:
                # No more listings, stop
                break

        # Remove duplicates
        all_listing_ids = list(set(all_listing_ids))
        logger.info(f"Total unique listings found: {len(all_listing_ids)}")

        # Scrape all listings
        return self.scrape_listings_batch(all_listing_ids)

    def discover_popular_shops(self, category_url: str, min_sales: int = 1000) -> List[str]:
        """
        Discover popular shops from a category page

        Args:
            category_url: URL of the category page
            min_sales: Minimum sales threshold for a shop to be considered popular

        Returns:
            List of shop names
        """
        logger.info(f"Discovering popular shops from: {category_url}")

        # Get listings from category
        listing_ids = self.scrape_page(category_url)

        # Scrape listings to get shop names
        listings = self.scrape_listings_batch(listing_ids)

        # Collect unique shops with enough sales
        popular_shops = set()

        for listing in listings:
            if listing.get('shop_name') and listing.get('sales_count', 0) >= min_sales:
                popular_shops.add(listing['shop_name'])

        logger.info(f"Found {len(popular_shops)} popular shops")
        return list(popular_shops)

    def close(self):
        """Close the scraper and cleanup resources"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
