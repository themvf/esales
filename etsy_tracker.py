from bs4 import BeautifulSoup
import requests
import json
import os
from datetime import datetime
import time
import re
from pathlib import Path


class EtsyShopTracker:
    """Track Etsy shop sales and products over time."""

    def __init__(self, config_file='stores.json', data_dir='data'):
        """
        Initialize the Etsy Shop Tracker.

        Args:
            config_file: Path to JSON file containing store configurations
            data_dir: Directory to store tracking data
        """
        self.config_file = config_file
        self.data_dir = data_dir
        self.stores = self._load_stores()
        self._ensure_data_dir()

    def _load_stores(self):
        """Load store configurations from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('stores', [])
        except FileNotFoundError:
            print(f"Error: Config file '{self.config_file}' not found.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{self.config_file}'.")
            return []

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        Path(self.data_dir).mkdir(exist_ok=True)

    def get_shop_info(self, shop_url):
        """
        Scrape information about an Etsy shop.

        Args:
            shop_url: URL of the Etsy shop

        Returns:
            Dictionary containing shop information
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(shop_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            shop_info = {
                'url': shop_url,
                'timestamp': datetime.now().isoformat(),
                'total_sales': None,
                'products': [],
                'error': None
            }

            # Try to find total shop sales
            # Etsy shows shop sales in various places, we'll try multiple methods
            sales_text = None

            # Method 1: Look for sales count in shop header
            sales_elements = soup.find_all(string=re.compile(r'\d+\s+sales', re.IGNORECASE))
            if sales_elements:
                for elem in sales_elements:
                    match = re.search(r'([\d,]+)\s+sales?', elem, re.IGNORECASE)
                    if match:
                        sales_text = match.group(1).replace(',', '')
                        try:
                            shop_info['total_sales'] = int(sales_text)
                            break
                        except ValueError:
                            pass

            return shop_info

        except requests.RequestException as e:
            return {
                'url': shop_url,
                'timestamp': datetime.now().isoformat(),
                'total_sales': None,
                'products': [],
                'error': str(e)
            }

    def get_shop_products(self, shop_url, max_pages=5):
        """
        Get product listings from a shop.

        Args:
            shop_url: URL of the Etsy shop
            max_pages: Maximum number of pages to scrape

        Returns:
            List of product dictionaries
        """
        products = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            for page in range(1, max_pages + 1):
                # Construct page URL
                if page == 1:
                    url = shop_url
                else:
                    url = f"{shop_url}?page={page}"

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'lxml')

                # Find all product listings
                listing_ids = []
                listings = soup.find_all("a")
                for tag in listings:
                    if tag.has_attr("data-listing-id"):
                        listing_id = tag["data-listing-id"]
                        if listing_id not in listing_ids:
                            listing_ids.append(listing_id)

                if not listing_ids:
                    break  # No more products found

                # Get details for each product
                for listing_id in listing_ids:
                    product = self.get_product_info(listing_id)
                    if product:
                        products.append(product)
                    time.sleep(0.5)  # Be respectful with requests

                time.sleep(1)  # Delay between pages

        except Exception as e:
            print(f"Error getting products: {e}")

        return products

    def get_product_info(self, listing_id):
        """
        Get detailed information about a specific product.

        Args:
            listing_id: Etsy listing ID

        Returns:
            Dictionary containing product information
        """
        try:
            listing_url = f"https://www.etsy.com/listing/{listing_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(listing_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            product = {
                'listing_id': listing_id,
                'url': listing_url,
                'title': None,
                'price': None,
                'sales': None,
                'timestamp': datetime.now().isoformat()
            }

            # Get product title
            title_tag = soup.find('h1')
            if title_tag:
                product['title'] = title_tag.get_text(strip=True)

            # Get price
            price_tag = soup.find('p', class_='wt-text-title-03')
            if price_tag:
                product['price'] = price_tag.get_text(strip=True)

            # Get number of sales
            regex = re.compile(r'\bsales?\b', re.IGNORECASE)
            span_tag = soup.find('span', class_='wt-text-caption', string=regex)
            if span_tag:
                sales_text = span_tag.get_text(strip=True)
                match = re.search(r'([\d,]+)\s+sales?', sales_text, re.IGNORECASE)
                if match:
                    try:
                        product['sales'] = int(match.group(1).replace(',', ''))
                    except ValueError:
                        pass

            return product

        except Exception as e:
            print(f"Error getting product {listing_id}: {e}")
            return None

    def track_store(self, store_config, track_products=True):
        """
        Track a single store and save the data.

        Args:
            store_config: Dictionary with store configuration
            track_products: Whether to track individual products

        Returns:
            Dictionary with tracking results
        """
        shop_name = store_config.get('shop_name', 'unknown')
        shop_url = store_config.get('url')

        print(f"\nTracking: {store_config.get('name', shop_name)}")
        print(f"URL: {shop_url}")

        # Get shop info
        shop_info = self.get_shop_info(shop_url)

        # Get products if enabled
        if track_products:
            print(f"Fetching products for {shop_name}...")
            products = self.get_shop_products(shop_url, max_pages=3)
            shop_info['products'] = products
            print(f"Found {len(products)} products")

        # Print summary
        if shop_info['total_sales'] is not None:
            print(f"Total shop sales: {shop_info['total_sales']:,}")
        else:
            print("Total shop sales: Unable to retrieve")

        if shop_info['error']:
            print(f"Error: {shop_info['error']}")

        # Save data
        self._save_tracking_data(shop_name, shop_info)

        return shop_info

    def _save_tracking_data(self, shop_name, data):
        """
        Save tracking data to JSON file.

        Args:
            shop_name: Name of the shop
            data: Data to save
        """
        # Create shop-specific file
        filename = f"{shop_name}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.data_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        # Also append to historical log
        history_file = os.path.join(self.data_dir, f"{shop_name}_history.jsonl")
        with open(history_file, 'a') as f:
            f.write(json.dumps(data) + '\n')

    def track_all_stores(self, track_products=True):
        """
        Track all enabled stores.

        Args:
            track_products: Whether to track individual products

        Returns:
            List of tracking results
        """
        results = []
        enabled_stores = [s for s in self.stores if s.get('enabled', True)]

        print(f"Tracking {len(enabled_stores)} stores...")

        for i, store in enumerate(enabled_stores, 1):
            print(f"\n[{i}/{len(enabled_stores)}] ", end="")
            result = self.track_store(store, track_products=track_products)
            results.append(result)

            # Be respectful with requests
            if i < len(enabled_stores):
                time.sleep(2)

        return results

    def get_daily_report(self):
        """
        Generate a daily report comparing today's data with previous data.

        Returns:
            Dictionary with report data
        """
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'stores': []
        }

        for store in self.stores:
            if not store.get('enabled', True):
                continue

            shop_name = store.get('shop_name')

            # Get today's data
            today_file = os.path.join(
                self.data_dir,
                f"{shop_name}_{datetime.now().strftime('%Y%m%d')}.json"
            )

            if os.path.exists(today_file):
                with open(today_file, 'r') as f:
                    today_data = json.load(f)

                store_report = {
                    'name': store.get('name'),
                    'shop_name': shop_name,
                    'total_sales': today_data.get('total_sales'),
                    'products_tracked': len(today_data.get('products', [])),
                }

                report['stores'].append(store_report)

        return report


def main():
    """Main function to run the tracker."""
    tracker = EtsyShopTracker()

    print("=" * 60)
    print("ETSY SHOP TRACKER")
    print("=" * 60)

    # Track all stores
    results = tracker.track_all_stores(track_products=True)

    # Generate report
    print("\n" + "=" * 60)
    print("DAILY REPORT")
    print("=" * 60)
    report = tracker.get_daily_report()
    print(f"\nDate: {report['date']}")
    print(f"\nStores tracked: {len(report['stores'])}")

    for store in report['stores']:
        print(f"\n{store['name']} ({store['shop_name']})")
        if store['total_sales'] is not None:
            print(f"  Total Sales: {store['total_sales']:,}")
        print(f"  Products Tracked: {store['products_tracked']}")

    print("\n" + "=" * 60)
    print(f"Data saved to '{tracker.data_dir}/' directory")
    print("=" * 60)


if __name__ == '__main__':
    main()
