"""
Database module for Etsy Sales Tracker
Handles SQLite database operations for shops, listings, and sales snapshots
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json


class Database:
    """Database manager for Etsy sales tracking"""

    def __init__(self, db_path: str = "data/etsy_sales.db"):
        """Initialize database connection"""
        self.db_path = db_path
        # Create data directory if it doesn't exist and is writable
        try:
            dir_path = os.path.dirname(db_path)
            if dir_path:  # Only create if there's a directory component
                os.makedirs(dir_path, exist_ok=True)
        except (OSError, PermissionError):
            # If we can't create the directory, use current directory
            self.db_path = os.path.basename(db_path)
        self.conn = None
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        if self.conn is None:
            # Use check_same_thread=False for Streamlit compatibility
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create shops table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                shop_name TEXT PRIMARY KEY,
                total_sales INTEGER DEFAULT 0,
                num_listings INTEGER DEFAULT 0,
                location TEXT,
                shop_url TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create listings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                listing_id TEXT PRIMARY KEY,
                shop_name TEXT,
                title TEXT,
                price REAL,
                currency TEXT DEFAULT 'USD',
                tags TEXT,  -- Stored as JSON array
                description TEXT,
                image_url TEXT,
                listing_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_name) REFERENCES shops(shop_name)
            )
        """)

        # Create sales_snapshots table for historical tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT,
                sales_count INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
            )
        """)

        # Create shop_snapshots table for shop-level historical tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_name TEXT,
                total_sales INTEGER DEFAULT 0,
                num_listings INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_name) REFERENCES shops(shop_name)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_listing_timestamp
            ON sales_snapshots(listing_id, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shop_snapshots_timestamp
            ON shop_snapshots(shop_name, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_listings_shop
            ON listings(shop_name)
        """)

        conn.commit()

    # ============ SHOP OPERATIONS ============

    def add_shop(self, shop_name: str, total_sales: int = 0, num_listings: int = 0,
                 location: str = None, shop_url: str = None):
        """Add or update a shop"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO shops (shop_name, total_sales, num_listings, location, shop_url, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(shop_name) DO UPDATE SET
                total_sales = excluded.total_sales,
                num_listings = excluded.num_listings,
                location = excluded.location,
                shop_url = excluded.shop_url,
                last_updated = CURRENT_TIMESTAMP
        """, (shop_name, total_sales, num_listings, location, shop_url))

        conn.commit()

    def get_shop(self, shop_name: str) -> Optional[Dict]:
        """Get shop information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM shops WHERE shop_name = ?", (shop_name,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_all_shops(self) -> List[Dict]:
        """Get all tracked shops"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM shops ORDER BY total_sales DESC")
        return [dict(row) for row in cursor.fetchall()]

    def delete_shop(self, shop_name: str):
        """Delete a shop and all associated data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Delete snapshots for all listings from this shop
        cursor.execute("""
            DELETE FROM sales_snapshots
            WHERE listing_id IN (
                SELECT listing_id FROM listings WHERE shop_name = ?
            )
        """, (shop_name,))

        # Delete listings
        cursor.execute("DELETE FROM listings WHERE shop_name = ?", (shop_name,))

        # Delete shop
        cursor.execute("DELETE FROM shops WHERE shop_name = ?", (shop_name,))

        conn.commit()

    # ============ LISTING OPERATIONS ============

    def add_listing(self, listing_id: str, shop_name: str, title: str = None,
                   price: float = None, currency: str = 'USD', tags: List[str] = None,
                   description: str = None, image_url: str = None, listing_url: str = None):
        """Add or update a listing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Convert tags list to JSON string
        tags_json = json.dumps(tags) if tags else None

        cursor.execute("""
            INSERT INTO listings (listing_id, shop_name, title, price, currency, tags,
                                 description, image_url, listing_url, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(listing_id) DO UPDATE SET
                shop_name = excluded.shop_name,
                title = excluded.title,
                price = excluded.price,
                currency = excluded.currency,
                tags = excluded.tags,
                description = excluded.description,
                image_url = excluded.image_url,
                listing_url = excluded.listing_url,
                last_updated = CURRENT_TIMESTAMP
        """, (listing_id, shop_name, title, price, currency, tags_json,
              description, image_url, listing_url))

        conn.commit()

    def get_listing(self, listing_id: str) -> Optional[Dict]:
        """Get listing information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM listings WHERE listing_id = ?", (listing_id,))
        row = cursor.fetchone()

        if row:
            listing = dict(row)
            # Parse tags JSON back to list
            if listing['tags']:
                listing['tags'] = json.loads(listing['tags'])
            return listing
        return None

    def get_listings_by_shop(self, shop_name: str) -> List[Dict]:
        """Get all listings for a shop"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM listings WHERE shop_name = ? ORDER BY created_at DESC",
                      (shop_name,))

        listings = []
        for row in cursor.fetchall():
            listing = dict(row)
            if listing['tags']:
                listing['tags'] = json.loads(listing['tags'])
            listings.append(listing)

        return listings

    def get_all_listings(self) -> List[Dict]:
        """Get all listings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM listings ORDER BY last_updated DESC")

        listings = []
        for row in cursor.fetchall():
            listing = dict(row)
            if listing['tags']:
                listing['tags'] = json.loads(listing['tags'])
            listings.append(listing)

        return listings

    # ============ SNAPSHOT OPERATIONS ============

    def add_snapshot(self, listing_id: str, sales_count: int = 0,
                    views: int = 0, favorites: int = 0):
        """Add a sales snapshot for a listing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sales_snapshots (listing_id, sales_count, views, favorites)
            VALUES (?, ?, ?, ?)
        """, (listing_id, sales_count, views, favorites))

        conn.commit()

    def get_latest_snapshot(self, listing_id: str) -> Optional[Dict]:
        """Get the most recent snapshot for a listing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sales_snapshots
            WHERE listing_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (listing_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_snapshots_by_listing(self, listing_id: str, limit: int = None) -> List[Dict]:
        """Get all snapshots for a listing, optionally limited"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM sales_snapshots
            WHERE listing_id = ?
            ORDER BY timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (listing_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_snapshot_at_date(self, listing_id: str, date: datetime) -> Optional[Dict]:
        """Get the closest snapshot before or at a specific date"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sales_snapshots
            WHERE listing_id = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (listing_id, date.isoformat()))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ============ SHOP SNAPSHOT OPERATIONS ============

    def add_shop_snapshot(self, shop_name: str, total_sales: int = 0, num_listings: int = 0):
        """Add a snapshot for shop-level tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO shop_snapshots (shop_name, total_sales, num_listings)
            VALUES (?, ?, ?)
        """, (shop_name, total_sales, num_listings))

        conn.commit()

    def get_shop_snapshots(self, shop_name: str, limit: int = None) -> List[Dict]:
        """Get all snapshots for a shop, optionally limited"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM shop_snapshots
            WHERE shop_name = ?
            ORDER BY timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (shop_name,))
        return [dict(row) for row in cursor.fetchall()]

    def get_shop_daily_sales(self, shop_name: str) -> Optional[int]:
        """Calculate sales in the last 24 hours for a shop"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get latest snapshot
        cursor.execute("""
            SELECT total_sales FROM shop_snapshots
            WHERE shop_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (shop_name,))

        current = cursor.fetchone()
        if not current:
            return None

        # Get snapshot from ~24 hours ago
        cursor.execute("""
            SELECT total_sales FROM shop_snapshots
            WHERE shop_name = ?
            AND timestamp <= datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 1
        """, (shop_name,))

        yesterday = cursor.fetchone()

        if yesterday:
            return current['total_sales'] - yesterday['total_sales']
        else:
            # If no data from 24 hours ago, return current count
            return current['total_sales']

    def get_all_shop_snapshots_latest(self) -> List[Dict]:
        """Get the latest snapshot for all shops"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, ss.total_sales as snapshot_sales, ss.timestamp as snapshot_time
            FROM shops s
            LEFT JOIN (
                SELECT shop_name, total_sales, timestamp
                FROM shop_snapshots ss1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM shop_snapshots ss2
                    WHERE ss2.shop_name = ss1.shop_name
                )
            ) ss ON s.shop_name = ss.shop_name
            ORDER BY s.total_sales DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    # ============ ANALYTICS QUERIES ============

    def get_seven_day_sales(self, listing_id: str) -> Optional[int]:
        """Calculate sales in the last 7 days for a listing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sales_count FROM sales_snapshots
            WHERE listing_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (listing_id,))

        current = cursor.fetchone()
        if not current:
            return None

        cursor.execute("""
            SELECT sales_count FROM sales_snapshots
            WHERE listing_id = ?
            AND timestamp <= datetime('now', '-7 days')
            ORDER BY timestamp DESC
            LIMIT 1
        """, (listing_id,))

        week_ago = cursor.fetchone()

        if week_ago:
            return current['sales_count'] - week_ago['sales_count']
        else:
            # If no data from 7 days ago, return current count
            return current['sales_count']

    def get_top_performing_listings(self, limit: int = 50) -> List[Dict]:
        """Get top performing listings by 7-day sales"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            WITH latest_snapshots AS (
                SELECT
                    listing_id,
                    sales_count as current_sales,
                    timestamp as current_time
                FROM sales_snapshots s1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM sales_snapshots s2
                    WHERE s2.listing_id = s1.listing_id
                )
            ),
            week_ago_snapshots AS (
                SELECT
                    listing_id,
                    sales_count as week_ago_sales
                FROM sales_snapshots s1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM sales_snapshots s2
                    WHERE s2.listing_id = s1.listing_id
                    AND s2.timestamp <= datetime('now', '-7 days')
                )
            )
            SELECT
                l.listing_id,
                l.shop_name,
                l.title,
                l.price,
                ls.current_sales,
                COALESCE(ls.current_sales - COALESCE(ws.week_ago_sales, 0), ls.current_sales) as seven_day_sales
            FROM listings l
            JOIN latest_snapshots ls ON l.listing_id = ls.listing_id
            LEFT JOIN week_ago_snapshots ws ON l.listing_id = ws.listing_id
            ORDER BY seven_day_sales DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_trending_tags(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular tags from top performing listings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT tags FROM listings WHERE tags IS NOT NULL")

        tag_counts = {}
        for row in cursor.fetchall():
            tags = json.loads(row['tags'])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count and return top N
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tags[:limit]

    def get_shop_stats(self, shop_name: str) -> Dict:
        """Get comprehensive stats for a shop"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get shop basic info
        shop = self.get_shop(shop_name)
        if not shop:
            return None

        # Get total listings
        cursor.execute("SELECT COUNT(*) as count FROM listings WHERE shop_name = ?",
                      (shop_name,))
        num_listings = cursor.fetchone()['count']

        # Get total sales from latest snapshots
        cursor.execute("""
            SELECT SUM(s.sales_count) as total_sales
            FROM (
                SELECT DISTINCT listing_id,
                       FIRST_VALUE(sales_count) OVER (
                           PARTITION BY listing_id ORDER BY timestamp DESC
                       ) as sales_count
                FROM sales_snapshots
                WHERE listing_id IN (
                    SELECT listing_id FROM listings WHERE shop_name = ?
                )
            ) s
        """, (shop_name,))

        total_sales_row = cursor.fetchone()
        total_sales = total_sales_row['total_sales'] if total_sales_row['total_sales'] else 0

        return {
            'shop_name': shop_name,
            'total_sales': total_sales,
            'num_listings': num_listings,
            'location': shop.get('location'),
            'first_seen': shop.get('first_seen'),
            'last_updated': shop.get('last_updated')
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
