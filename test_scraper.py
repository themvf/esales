"""
Diagnostic script to test Etsy scraping and debug extraction issues
"""

import sys
import logging
from scraper import EtsyScraper
from database import Database

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_shop_scrape(shop_name):
    """Test scraping a single shop"""
    print(f"\n{'='*60}")
    print(f"Testing shop: {shop_name}")
    print(f"{'='*60}\n")

    scraper = EtsyScraper(delay=2.0)

    # Test shop scraping
    print("1. Scraping shop info...")
    shop_info = scraper.scrape_shop(shop_name)

    if shop_info:
        print("\n✅ Shop Info Extracted:")
        for key, value in shop_info.items():
            print(f"  {key}: {value}")
    else:
        print("\n❌ Failed to extract shop info")

    # Test listing scraping
    print("\n2. Scraping shop listings (first 3)...")
    listings = scraper.scrape_shop_listings(shop_name, max_listings=3)

    if listings:
        print(f"\n✅ Found {len(listings)} listings:")
        for i, listing in enumerate(listings, 1):
            print(f"\n  Listing {i}:")
            print(f"    ID: {listing.get('listing_id')}")
            print(f"    Title: {listing.get('title', 'N/A')}")
            print(f"    Price: ${listing.get('price', 'N/A')}")
            print(f"    Sales: {listing.get('sales_count', 'N/A')}")
            print(f"    Tags: {listing.get('tags', [])[:5]}")  # First 5 tags
    else:
        print("\n❌ Failed to extract listings")

    scraper.close()

    return shop_info, listings


def check_database():
    """Check what's in the database"""
    print(f"\n{'='*60}")
    print("Database Contents")
    print(f"{'='*60}\n")

    db = Database()

    shops = db.get_all_shops()
    print(f"Total shops tracked: {len(shops)}\n")

    for shop in shops:
        print(f"Shop: {shop['shop_name']}")
        print(f"  Total Sales: {shop['total_sales']}")
        print(f"  Listings: {shop['num_listings']}")
        print(f"  Last Updated: {shop['last_updated']}")

        # Get listings for this shop
        listings = db.get_listings_by_shop(shop['shop_name'])
        print(f"  Listings in DB: {len(listings)}")

        if listings:
            # Check snapshots for first listing
            first_listing = listings[0]
            snapshot = db.get_latest_snapshot(first_listing['listing_id'])
            if snapshot:
                print(f"  Latest snapshot sales: {snapshot['sales_count']}")
        print()

    db.close()


if __name__ == '__main__':
    # Check current database state
    check_database()

    # Test scraping if shop name provided
    if len(sys.argv) > 1:
        shop_name = sys.argv[1]
        shop_info, listings = test_shop_scrape(shop_name)

        # Optionally save to database
        if shop_info or listings:
            print("\n" + "="*60)
            response = input("Save to database? (y/n): ")
            if response.lower() == 'y':
                db = Database()

                if shop_info:
                    db.add_shop(
                        shop_name=shop_info.get('shop_name', shop_name),
                        total_sales=shop_info.get('total_sales', 0),
                        num_listings=shop_info.get('num_listings', 0),
                        location=shop_info.get('location'),
                        shop_url=shop_info.get('shop_url')
                    )
                    print("✅ Shop saved to database")

                if listings:
                    for listing in listings:
                        db.add_listing(
                            listing_id=listing.get('listing_id'),
                            shop_name=listing.get('shop_name', shop_name),
                            title=listing.get('title'),
                            price=listing.get('price'),
                            tags=listing.get('tags', [])
                        )

                        db.add_snapshot(
                            listing_id=listing.get('listing_id'),
                            sales_count=listing.get('sales_count', 0)
                        )
                    print(f"✅ {len(listings)} listings saved to database")

                db.close()
    else:
        print("\n💡 Usage: python test_scraper.py <shop_name>")
        print("   Example: python test_scraper.py TheClayPlay")
