"""
Insights Generation Module
Advanced analytics and intelligence for Etsy sales data
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

from database import Database

logger = logging.getLogger(__name__)


def get_trending_products(db: Database, lookback_days: int = 7, min_sales: int = 5, limit: int = 20) -> List[Dict]:
    """
    Identify products with accelerating sales (trending up)

    Args:
        db: Database instance
        lookback_days: Number of days to analyze
        min_sales: Minimum sales in period to be considered
        limit: Maximum number of results

    Returns:
        List of trending products with metrics
    """
    all_listings = db.get_all_listings()
    trending = []

    for listing in all_listings:
        listing_id = listing['listing_id']

        # Get recent snapshots
        snapshots = db.get_snapshots_by_listing(listing_id, limit=lookback_days * 2)

        if len(snapshots) < 2:
            continue

        # Get sales from most recent and from lookback_days ago
        recent_sales = snapshots[0]['sales_count']

        # Find snapshot from lookback_days ago
        lookback_date = datetime.now() - timedelta(days=lookback_days)
        old_snapshot = db.get_snapshot_at_date(listing_id, lookback_date)

        if not old_snapshot:
            continue

        old_sales = old_snapshot['sales_count']
        sales_increase = recent_sales - old_sales

        if sales_increase < min_sales:
            continue

        # Calculate acceleration (compare first half vs second half of period)
        mid_point = len(snapshots) // 2
        if mid_point > 0:
            recent_half_sales = snapshots[0]['sales_count'] - snapshots[mid_point]['sales_count']
            old_half_sales = snapshots[mid_point]['sales_count'] - snapshots[-1]['sales_count']

            # Calculate acceleration factor
            if old_half_sales > 0:
                acceleration = recent_half_sales / old_half_sales
            else:
                acceleration = recent_half_sales  # If old is 0, just use recent

            trending.append({
                'listing_id': listing_id,
                'title': listing['title'],
                'shop_name': listing['shop_name'],
                'sales_increase': sales_increase,
                'acceleration': acceleration,
                'current_sales': recent_sales,
                'price': listing['price']
            })

    # Sort by acceleration and sales increase
    trending.sort(key=lambda x: (x['acceleration'], x['sales_increase']), reverse=True)

    return trending[:limit]


def find_emerging_keywords(db: Database, lookback_days: int = 14, min_occurrences: int = 3) -> List[Dict]:
    """
    Detect tags/keywords that are gaining popularity

    Args:
        db: Database instance
        lookback_days: Number of days to analyze
        min_occurrences: Minimum occurrences to be considered

    Returns:
        List of emerging keywords with growth metrics
    """
    # Get listings created/updated in the lookback period
    all_listings = db.get_all_listings()

    # Separate recent vs older listings
    recent_cutoff = datetime.now() - timedelta(days=lookback_days)
    recent_tags = Counter()
    older_tags = Counter()

    for listing in all_listings:
        if not listing['tags']:
            continue

        try:
            last_updated = datetime.fromisoformat(listing['last_updated'].replace('Z', '+00:00'))
        except:
            continue

        tags = listing['tags']

        if last_updated >= recent_cutoff:
            recent_tags.update(tags)
        else:
            older_tags.update(tags)

    # Find tags that are more common in recent listings
    emerging = []

    for tag, recent_count in recent_tags.items():
        if recent_count < min_occurrences:
            continue

        older_count = older_tags.get(tag, 0)

        # Calculate growth rate
        if older_count > 0:
            growth_rate = (recent_count - older_count) / older_count
        else:
            growth_rate = float('inf')  # New tag

        emerging.append({
            'tag': tag,
            'recent_count': recent_count,
            'older_count': older_count,
            'growth_rate': growth_rate
        })

    # Sort by growth rate
    emerging.sort(key=lambda x: (x['growth_rate'], x['recent_count']), reverse=True)

    return emerging


def calculate_shop_rankings(db: Database, metric: str = 'sales_velocity') -> List[Dict]:
    """
    Rank shops by various metrics

    Args:
        db: Database instance
        metric: Metric to rank by ('sales_velocity', 'total_sales', 'num_listings', 'avg_price')

    Returns:
        List of shops with rankings
    """
    all_shops = db.get_all_shops()
    rankings = []

    for shop in all_shops:
        shop_name = shop['shop_name']
        stats = db.get_shop_stats(shop_name)

        if not stats:
            continue

        # Calculate metrics
        total_sales = stats['total_sales']
        num_listings = stats['num_listings']

        # Get 7-day sales for shop
        listings = db.get_listings_by_shop(shop_name)
        seven_day_sales = 0

        for listing in listings:
            sales = db.get_seven_day_sales(listing['listing_id'])
            if sales:
                seven_day_sales += sales

        # Calculate sales velocity (7-day sales as % of total)
        if total_sales > 0:
            sales_velocity = (seven_day_sales / total_sales) * 100
        else:
            sales_velocity = 0

        # Calculate average price
        avg_price = 0
        if listings:
            prices = [l['price'] for l in listings if l['price']]
            if prices:
                avg_price = statistics.mean(prices)

        rankings.append({
            'shop_name': shop_name,
            'total_sales': total_sales,
            'num_listings': num_listings,
            'seven_day_sales': seven_day_sales,
            'sales_velocity': sales_velocity,
            'avg_price': avg_price
        })

    # Sort by selected metric
    if metric in ['total_sales', 'num_listings', 'seven_day_sales', 'sales_velocity', 'avg_price']:
        rankings.sort(key=lambda x: x[metric], reverse=True)

    # Add rank
    for i, shop in enumerate(rankings, 1):
        shop['rank'] = i

    return rankings


def suggest_price_ranges(db: Database, category_tag: str = None, percentiles: List[int] = [25, 50, 75]) -> Dict:
    """
    Analyze pricing strategies of top sellers

    Args:
        db: Database instance
        category_tag: Optional tag to filter by category
        percentiles: Percentiles to calculate

    Returns:
        Dictionary with price range suggestions
    """
    # Get top performing listings
    top_listings = db.get_top_performing_listings(limit=100)

    if not top_listings:
        return {}

    # Filter by category if specified
    if category_tag:
        all_listings_info = db.get_all_listings()
        filtered_ids = [
            l['listing_id'] for l in all_listings_info
            if l['tags'] and category_tag.lower() in [t.lower() for t in l['tags']]
        ]
        top_listings = [l for l in top_listings if l['listing_id'] in filtered_ids]

    if not top_listings:
        return {}

    # Extract prices
    prices = [l['price'] for l in top_listings if l.get('price')]

    if not prices:
        return {}

    # Calculate statistics
    result = {
        'min': min(prices),
        'max': max(prices),
        'mean': statistics.mean(prices),
        'median': statistics.median(prices),
        'percentiles': {}
    }

    # Calculate percentiles
    sorted_prices = sorted(prices)
    for p in percentiles:
        idx = int(len(sorted_prices) * p / 100)
        result['percentiles'][p] = sorted_prices[idx]

    # Price range recommendations
    result['recommendations'] = {
        'budget': (result['min'], result['percentiles'].get(25, result['median'])),
        'mid_range': (result['percentiles'].get(25, result['median']), result['percentiles'].get(75, result['median'])),
        'premium': (result['percentiles'].get(75, result['median']), result['max'])
    }

    return result


def detect_seasonal_trends(db: Database, listing_id: str = None) -> Dict:
    """
    Identify seasonal patterns in sales data

    Args:
        db: Database instance
        listing_id: Optional specific listing to analyze (None for all)

    Returns:
        Dictionary with seasonal insights
    """
    # This is a simplified version - would need more historical data for real seasonal analysis
    if listing_id:
        snapshots = db.get_snapshots_by_listing(listing_id)
    else:
        # Get all snapshots (would need to be implemented in DB)
        snapshots = []

    if len(snapshots) < 30:  # Need at least 30 days of data
        return {
            'status': 'insufficient_data',
            'message': 'Need at least 30 days of data for seasonal analysis'
        }

    # Group by day of week, month, etc.
    day_sales = defaultdict(list)
    month_sales = defaultdict(list)

    for i in range(len(snapshots) - 1):
        current = snapshots[i]
        previous = snapshots[i + 1]

        daily_sales = current['sales_count'] - previous['sales_count']

        try:
            date = datetime.fromisoformat(current['timestamp'].replace('Z', '+00:00'))
            day_sales[date.strftime('%A')].append(daily_sales)
            month_sales[date.month].append(daily_sales)
        except:
            continue

    # Calculate averages
    avg_by_day = {day: statistics.mean(sales) for day, sales in day_sales.items() if sales}
    avg_by_month = {month: statistics.mean(sales) for month, sales in month_sales.items() if sales}

    # Find best days/months
    best_day = max(avg_by_day, key=avg_by_day.get) if avg_by_day else None
    best_month = max(avg_by_month, key=avg_by_month.get) if avg_by_month else None

    return {
        'status': 'success',
        'avg_by_day': avg_by_day,
        'avg_by_month': avg_by_month,
        'best_day': best_day,
        'best_month': best_month
    }


def generate_competitive_analysis(db: Database, shop_name: str, competitor_shops: List[str] = None) -> Dict:
    """
    Compare a shop against competitors

    Args:
        db: Database instance
        shop_name: Shop to analyze
        competitor_shops: List of competitor shop names (None for top shops)

    Returns:
        Dictionary with competitive insights
    """
    # Get target shop stats
    target_stats = db.get_shop_stats(shop_name)

    if not target_stats:
        return {'error': f'Shop {shop_name} not found'}

    # Get competitors (either specified or top shops)
    if not competitor_shops:
        all_rankings = calculate_shop_rankings(db, metric='seven_day_sales')
        competitor_shops = [r['shop_name'] for r in all_rankings[:10] if r['shop_name'] != shop_name]

    competitor_stats = []
    for comp_shop in competitor_shops:
        stats = db.get_shop_stats(comp_shop)
        if stats:
            # Get 7-day sales
            listings = db.get_listings_by_shop(comp_shop)
            seven_day = 0
            for listing in listings:
                sales = db.get_seven_day_sales(listing['listing_id'])
                if sales:
                    seven_day += sales
            stats['seven_day_sales'] = seven_day
            competitor_stats.append(stats)

    # Calculate target shop's 7-day sales
    target_listings = db.get_listings_by_shop(shop_name)
    target_seven_day = 0
    for listing in target_listings:
        sales = db.get_seven_day_sales(listing['listing_id'])
        if sales:
            target_seven_day += sales

    # Compare metrics
    avg_competitor_sales = statistics.mean([c['total_sales'] for c in competitor_stats]) if competitor_stats else 0
    avg_competitor_7day = statistics.mean([c['seven_day_sales'] for c in competitor_stats]) if competitor_stats else 0
    avg_competitor_listings = statistics.mean([c['num_listings'] for c in competitor_stats]) if competitor_stats else 0

    return {
        'shop_name': shop_name,
        'total_sales': target_stats['total_sales'],
        'seven_day_sales': target_seven_day,
        'num_listings': target_stats['num_listings'],
        'avg_competitor_sales': avg_competitor_sales,
        'avg_competitor_7day': avg_competitor_7day,
        'avg_competitor_listings': avg_competitor_listings,
        'sales_vs_avg': target_stats['total_sales'] / avg_competitor_sales if avg_competitor_sales > 0 else 0,
        '7day_vs_avg': target_seven_day / avg_competitor_7day if avg_competitor_7day > 0 else 0,
        'listings_vs_avg': target_stats['num_listings'] / avg_competitor_listings if avg_competitor_listings > 0 else 0,
        'competitors': competitor_stats
    }


def get_performance_insights(db: Database, shop_name: str = None) -> List[str]:
    """
    Generate actionable insights and recommendations

    Args:
        db: Database instance
        shop_name: Optional shop to analyze (None for general insights)

    Returns:
        List of insight strings
    """
    insights = []

    if shop_name:
        # Shop-specific insights
        stats = db.get_shop_stats(shop_name)

        if not stats:
            return [f"Shop {shop_name} not found in database"]

        # Analyze shop performance
        listings = db.get_listings_by_shop(shop_name)

        if not listings:
            insights.append(f"No listings found for {shop_name}. Start scraping to get data.")
            return insights

        # Check for low-performing listings
        low_performers = []
        high_performers = []

        for listing in listings:
            seven_day = db.get_seven_day_sales(listing['listing_id'])
            if seven_day is not None:
                if seven_day == 0:
                    low_performers.append(listing)
                elif seven_day > 5:
                    high_performers.append(listing)

        if low_performers:
            insights.append(f"⚠️ {len(low_performers)} listings have 0 sales in the last 7 days. Consider updating titles, tags, or images.")

        if high_performers:
            insights.append(f"✅ {len(high_performers)} listings are performing well with 5+ sales in 7 days. Analyze their tags and pricing.")

        # Price analysis
        prices = [l['price'] for l in listings if l['price']]
        if prices:
            avg_price = statistics.mean(prices)
            insights.append(f"💰 Your average listing price is ${avg_price:.2f}")

            # Compare with top performers
            top_listings = db.get_top_performing_listings(limit=50)
            top_prices = [l['price'] for l in top_listings if l.get('price')]
            if top_prices:
                avg_top_price = statistics.mean(top_prices)
                if avg_price < avg_top_price * 0.7:
                    insights.append(f"💡 Top performers average ${avg_top_price:.2f}. Consider premium pricing for high-quality items.")
                elif avg_price > avg_top_price * 1.3:
                    insights.append(f"💡 Your prices are above market average. Ensure value justifies premium pricing.")

    else:
        # General insights
        trending = get_trending_products(db, limit=5)
        if trending:
            insights.append(f"🔥 {len(trending)} products are trending with accelerating sales!")

        emerging = find_emerging_keywords(db, min_occurrences=2)
        if emerging:
            top_emerging = emerging[:3]
            tags = ', '.join([e['tag'] for e in top_emerging])
            insights.append(f"📈 Emerging keywords: {tags}")

        # Overall market insights
        all_shops = db.get_all_shops()
        if len(all_shops) > 5:
            insights.append(f"📊 Tracking {len(all_shops)} shops. Add more competitors to improve insights.")

    return insights if insights else ["No insights available yet. Add shops and let data accumulate."]
