"""
Re-scrape existing shops (shop-level tracking only)
Tracks total sales per shop without scraping individual listings
"""

import logging
import time
import argparse
from database import Database
from scraper.etsy_client import EtsyClient
from scraper.extractors_improved import extract_shop_info_improved

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def rescrape_shop(shop_name: str, db: Database, client: EtsyClient, max_listings: int = 0):
    """Re-scrape a single shop (shop-level only, no individual listings)"""
    logger.info(f"Re-scraping shop: {shop_name}")

    # Scrape shop page
    shop_url = f"https://www.etsy.com/shop/{shop_name}"
    response = client.get(shop_url)

    if not response:
        logger.error(f"Failed to fetch shop page: {shop_url}")
        return False

    # Extract shop info with improved extractor
    shop_info = extract_shop_info_improved(response.text, shop_name)

    total_sales = shop_info.get('total_sales', 0)
    num_listings = shop_info.get('num_listings', 0)

    # Update shop in database
    db.add_shop(
        shop_name=shop_info.get('shop_name', shop_name),
        total_sales=total_sales,
        num_listings=num_listings,
        location=shop_info.get('location'),
        shop_url=shop_url
    )

    # Add shop snapshot for historical tracking
    db.add_shop_snapshot(
        shop_name=shop_info.get('shop_name', shop_name),
        total_sales=total_sales,
        num_listings=num_listings
    )

    logger.info(f"  ✅ Total sales: {total_sales:,}")
    logger.info(f"  ✅ Listings: {num_listings:,}")
    logger.info(f"  ✅ Snapshot created")

    return True


def main():
    """Re-scrape all shops in database (shop-level tracking only)"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Re-scrape Etsy shops (shop-level tracking)')
    parser.add_argument('--max-listings', type=int, default=0,
                       help='[DEPRECATED] Not used for shop-level tracking')
    parser.add_argument('--shops', type=str, default='',
                       help='Comma-separated list of specific shops to scrape (default: all)')
    args = parser.parse_args()

    specific_shops = [s.strip() for s in args.shops.split(',') if s.strip()] if args.shops else None

    logger.info("=" * 60)
    logger.info("Starting shop-level scraping...")
    logger.info("Mode: Shop total sales tracking (no individual listings)")
    logger.info("=" * 60)

    db = Database()
    client = EtsyClient(delay=2.0)

    # Get all shops or filter by specific shops
    all_shops = db.get_all_shops()

    if not all_shops:
        logger.info("No shops in database to re-scrape")
        return

    # Filter shops if specific ones requested
    if specific_shops:
        shops = [s for s in all_shops if s['shop_name'] in specific_shops]
        logger.info(f"Scraping {len(shops)} specific shops: {', '.join([s['shop_name'] for s in shops])}\n")
    else:
        shops = all_shops
        logger.info(f"Found {len(shops)} shops to scrape\n")

    success_count = 0
    total_sales_scraped = 0

    for i, shop in enumerate(shops, 1):
        shop_name = shop['shop_name']

        logger.info(f"\n[{i}/{len(shops)}] Processing: {shop_name}")
        logger.info("-" * 60)

        try:
            if rescrape_shop(shop_name, db, client, max_listings=0):
                success_count += 1
                # Get the shop's total sales
                shop_data = db.get_shop(shop_name)
                if shop_data:
                    total_sales_scraped += shop_data.get('total_sales', 0)
            else:
                logger.error(f"Failed to scrape {shop_name}")
        except Exception as e:
            logger.error(f"Error scraping {shop_name}: {e}", exc_info=True)

        # Small delay between shops
        if i < len(shops):
            logger.info("Waiting 3 seconds before next shop...")
            time.sleep(3)

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Shop-level scraping complete!")
    logger.info(f"✅ Successfully scraped: {success_count}/{len(shops)} shops")
    logger.info(f"✅ Total sales across all shops: {total_sales_scraped:,}")
    logger.info(f"✅ Snapshots created for daily tracking")
    logger.info(f"{'='*60}")

    db.close()
    client.close()


if __name__ == '__main__':
    main()
