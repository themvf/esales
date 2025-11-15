"""
Re-scrape existing shops using improved extractors
This will update the database with correct sales data
"""

import logging
import time
import argparse
from database import Database
from scraper.etsy_client import EtsyClient
from scraper.extractors_improved import (
    extract_shop_info_improved,
    extract_listing_info_improved,
    extract_listing_ids_improved
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def rescrape_shop(shop_name: str, db: Database, client: EtsyClient, max_listings: int = 50):
    """Re-scrape a single shop with improved extractors"""
    logger.info(f"Re-scraping shop: {shop_name}")

    # Scrape shop page
    shop_url = f"https://www.etsy.com/shop/{shop_name}"
    response = client.get(shop_url)

    if not response:
        logger.error(f"Failed to fetch shop page: {shop_url}")
        return False

    # Extract shop info with improved extractor
    shop_info = extract_shop_info_improved(response.text, shop_name)

    # Update shop in database
    db.add_shop(
        shop_name=shop_info.get('shop_name', shop_name),
        total_sales=shop_info.get('total_sales', 0),
        num_listings=shop_info.get('num_listings', 0),
        location=shop_info.get('location'),
        shop_url=shop_url
    )

    logger.info(f"  Shop sales: {shop_info.get('total_sales', 0)}")
    logger.info(f"  Shop listings: {shop_info.get('num_listings', 0)}")

    # Extract listing IDs
    listing_ids = extract_listing_ids_improved(response.text)

    if not listing_ids:
        logger.warning(f"No listings found for {shop_name}")
        return True

    # Limit number of listings
    if max_listings:
        listing_ids = listing_ids[:max_listings]

    logger.info(f"  Scraping {len(listing_ids)} listings...")

    # Scrape each listing
    scraped_count = 0
    for i, listing_id in enumerate(listing_ids, 1):
        listing_url = f"https://www.etsy.com/listing/{listing_id}"

        response = client.get(listing_url)
        if not response:
            logger.warning(f"  Failed to fetch listing {listing_id}")
            continue

        # Extract listing info with improved extractor
        listing_info = extract_listing_info_improved(response.text, listing_id)

        # Save to database
        db.add_listing(
            listing_id=listing_id,
            shop_name=listing_info.get('shop_name', shop_name),
            title=listing_info.get('title'),
            price=listing_info.get('price'),
            currency=listing_info.get('currency', 'USD'),
            tags=listing_info.get('tags', []),
            description=listing_info.get('description'),
            image_url=listing_info.get('image_url'),
            listing_url=listing_url
        )

        # Add snapshot
        db.add_snapshot(
            listing_id=listing_id,
            sales_count=listing_info.get('sales_count', 0),
            views=listing_info.get('views', 0),
            favorites=listing_info.get('favorites', 0)
        )

        scraped_count += 1

        if i % 5 == 0:
            logger.info(f"  Progress: {i}/{len(listing_ids)} listings")

    logger.info(f"✅ Successfully scraped {scraped_count}/{len(listing_ids)} listings for {shop_name}")
    return True


def main():
    """Re-scrape all shops in database"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Re-scrape Etsy shops with improved extractors')
    parser.add_argument('--max-listings', type=int, default=50,
                       help='Maximum listings to scrape per shop (default: 50)')
    parser.add_argument('--shops', type=str, default='',
                       help='Comma-separated list of specific shops to scrape (default: all)')
    args = parser.parse_args()

    max_listings = args.max_listings
    specific_shops = [s.strip() for s in args.shops.split(',') if s.strip()] if args.shops else None

    logger.info("Starting re-scrape of shops...")
    logger.info(f"Max listings per shop: {max_listings}")

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
        logger.info(f"Found {len(shops)} shops to re-scrape\n")

    success_count = 0
    for i, shop in enumerate(shops, 1):
        shop_name = shop['shop_name']

        logger.info(f"\n[{i}/{len(shops)}] Processing: {shop_name}")
        logger.info("-" * 60)

        try:
            if rescrape_shop(shop_name, db, client, max_listings=max_listings):
                success_count += 1
            else:
                logger.error(f"Failed to re-scrape {shop_name}")
        except Exception as e:
            logger.error(f"Error re-scraping {shop_name}: {e}", exc_info=True)

        # Small delay between shops
        if i < len(shops):
            logger.info("Waiting 5 seconds before next shop...")
            time.sleep(5)

    logger.info(f"\n{'='*60}")
    logger.info(f"Re-scrape complete!")
    logger.info(f"Successfully re-scraped: {success_count}/{len(shops)} shops")
    logger.info(f"{'='*60}")

    db.close()
    client.close()


if __name__ == '__main__':
    main()
