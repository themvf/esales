"""
Analytics Module
Advanced analytics and insights generation for Etsy sales data
"""

from .insights import (
    get_trending_products,
    find_emerging_keywords,
    calculate_shop_rankings,
    suggest_price_ranges,
    detect_seasonal_trends,
    generate_competitive_analysis,
    get_performance_insights
)

__all__ = [
    'get_trending_products',
    'find_emerging_keywords',
    'calculate_shop_rankings',
    'suggest_price_ranges',
    'detect_seasonal_trends',
    'generate_competitive_analysis',
    'get_performance_insights'
]
