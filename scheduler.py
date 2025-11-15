"""
Scheduler Module
Handles automated scraping jobs and monitoring
"""

import logging
import time
import yaml
from datetime import datetime
from typing import List, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from database import Database
from scraper import EtsyScraper

logger = logging.getLogger(__name__)


class ScraperScheduler:
    """Manages scheduled scraping jobs"""

    def __init__(self, config_path: str = "config.yaml", db_path: str = "data/etsy_sales.db"):
        """
        Initialize scheduler

        Args:
            config_path: Path to configuration file
            db_path: Path to database file
        """
        self.config = self.load_config(config_path)
        self.db = Database(db_path)
        self.scheduler = BackgroundScheduler()
        self.scraper = None

    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'scraper': {
                'delay': 2.0,
                'max_workers': 5,
                'max_retries': 3
            },
            'scheduling': {
                'daily_scrape_hour': 2,  # 2 AM
                'daily_scrape_minute': 0,
                'enable_continuous': False,
                'interval_hours': 24
            },
            'shops': {
                'tracked_shops': [],
                'auto_discover': False,
                'min_sales_threshold': 1000
            },
            'database': {
                'path': 'data/etsy_sales.db'
            }
        }

    def initialize_scraper(self):
        """Initialize scraper with configuration"""
        if self.scraper is None:
            scraper_config = self.config.get('scraper', {})
            self.scraper = EtsyScraper(
                delay=scraper_config.get('delay', 2.0),
                max_workers=scraper_config.get('max_workers', 5)
            )

    def scrape_shop_job(self, shop_name: str):
        """
        Job to scrape a single shop and update database

        Args:
            shop_name: Name of the shop to scrape
        """
        logger.info(f"Starting scheduled scrape for shop: {shop_name}")

        try:
            self.initialize_scraper()

            # Scrape shop info
            shop_info = self.scraper.scrape_shop(shop_name)
            if shop_info:
                self.db.add_shop(
                    shop_name=shop_info.get('shop_name', shop_name),
                    total_sales=shop_info.get('total_sales', 0),
                    num_listings=shop_info.get('num_listings', 0),
                    location=shop_info.get('location'),
                    shop_url=shop_info.get('shop_url')
                )
                logger.info(f"Updated shop info for {shop_name}")

            # Scrape shop listings
            listings = self.scraper.scrape_shop_listings(shop_name)

            for listing in listings:
                # Add/update listing
                self.db.add_listing(
                    listing_id=listing.get('listing_id'),
                    shop_name=listing.get('shop_name', shop_name),
                    title=listing.get('title'),
                    price=listing.get('price'),
                    currency=listing.get('currency', 'USD'),
                    tags=listing.get('tags', []),
                    description=listing.get('description'),
                    image_url=listing.get('image_url'),
                    listing_url=listing.get('listing_url')
                )

                # Add snapshot
                self.db.add_snapshot(
                    listing_id=listing.get('listing_id'),
                    sales_count=listing.get('sales_count', 0),
                    views=listing.get('views', 0),
                    favorites=listing.get('favorites', 0)
                )

            logger.info(f"Successfully scraped {len(listings)} listings for {shop_name}")

        except Exception as e:
            logger.error(f"Error scraping shop {shop_name}: {e}", exc_info=True)

    def scrape_all_tracked_shops(self):
        """Job to scrape all tracked shops"""
        logger.info("Starting scheduled scrape for all tracked shops")

        # Get tracked shops from config
        tracked_shops = self.config.get('shops', {}).get('tracked_shops', [])

        # Also get shops from database
        db_shops = self.db.get_all_shops()
        for shop in db_shops:
            if shop['shop_name'] not in tracked_shops:
                tracked_shops.append(shop['shop_name'])

        logger.info(f"Scraping {len(tracked_shops)} tracked shops")

        for shop_name in tracked_shops:
            self.scrape_shop_job(shop_name)
            # Small delay between shops
            time.sleep(1)

        logger.info("Completed scheduled scrape for all tracked shops")

    def discover_and_track_shops(self):
        """Job to discover new popular shops"""
        if not self.config.get('shops', {}).get('auto_discover', False):
            logger.info("Auto-discovery is disabled")
            return

        logger.info("Starting shop discovery job")

        try:
            self.initialize_scraper()

            # Define some popular Etsy categories to search
            categories = [
                "https://www.etsy.com/c/jewelry",
                "https://www.etsy.com/c/home-and-living",
                "https://www.etsy.com/c/clothing",
                "https://www.etsy.com/c/art-and-collectibles"
            ]

            min_sales = self.config.get('shops', {}).get('min_sales_threshold', 1000)

            all_shops = set()
            for category_url in categories:
                shops = self.scraper.discover_popular_shops(category_url, min_sales=min_sales)
                all_shops.update(shops)
                time.sleep(5)  # Delay between categories

            logger.info(f"Discovered {len(all_shops)} popular shops")

            # Add discovered shops to database
            for shop_name in all_shops:
                # Check if shop already tracked
                existing_shop = self.db.get_shop(shop_name)
                if not existing_shop:
                    self.db.add_shop(shop_name)
                    logger.info(f"Added new shop to tracking: {shop_name}")

        except Exception as e:
            logger.error(f"Error during shop discovery: {e}", exc_info=True)

    def add_job(self, job_id: str, func, trigger, **kwargs):
        """
        Add a job to the scheduler

        Args:
            job_id: Unique identifier for the job
            func: Function to execute
            trigger: APScheduler trigger
            **kwargs: Additional arguments for add_job
        """
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            replace_existing=True,
            **kwargs
        )
        logger.info(f"Added job: {job_id}")

    def setup_scheduled_jobs(self):
        """Set up all scheduled jobs based on configuration"""
        schedule_config = self.config.get('scheduling', {})

        # Daily scraping job
        daily_hour = schedule_config.get('daily_scrape_hour', 2)
        daily_minute = schedule_config.get('daily_scrape_minute', 0)

        self.add_job(
            'daily_scrape_all_shops',
            self.scrape_all_tracked_shops,
            CronTrigger(hour=daily_hour, minute=daily_minute)
        )

        # Optional: Continuous scraping at intervals
        if schedule_config.get('enable_continuous', False):
            interval_hours = schedule_config.get('interval_hours', 24)
            self.add_job(
                'interval_scrape_all_shops',
                self.scrape_all_tracked_shops,
                IntervalTrigger(hours=interval_hours)
            )

        # Weekly shop discovery
        if self.config.get('shops', {}).get('auto_discover', False):
            self.add_job(
                'weekly_shop_discovery',
                self.discover_and_track_shops,
                CronTrigger(day_of_week='sun', hour=1, minute=0)
            )

        logger.info("Scheduled jobs configured")

    def start(self):
        """Start the scheduler"""
        self.setup_scheduled_jobs()
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

        if self.scraper:
            self.scraper.close()

        self.db.close()

    def run_once(self):
        """Run all tracked shops scraping once (for testing)"""
        logger.info("Running one-time scrape")
        self.scrape_all_tracked_shops()

    def add_shop_to_tracking(self, shop_name: str):
        """
        Add a shop to tracking list

        Args:
            shop_name: Name of the shop to track
        """
        # Add to database
        self.db.add_shop(shop_name)

        # Immediately scrape the shop
        self.scrape_shop_job(shop_name)

        logger.info(f"Added shop to tracking: {shop_name}")

    def get_status(self) -> Dict:
        """Get scheduler status"""
        jobs = self.scheduler.get_jobs()

        return {
            'running': self.scheduler.running,
            'num_jobs': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }


def main():
    """Main function for running scheduler"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create scheduler
    scheduler = ScraperScheduler()

    # Start scheduler
    scheduler.start()

    try:
        # Keep running
        logger.info("Scheduler is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(60)
            # Print status every minute
            status = scheduler.get_status()
            logger.info(f"Status: {status}")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.stop()


if __name__ == '__main__':
    main()
