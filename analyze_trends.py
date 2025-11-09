#!/usr/bin/env python3
"""
Analyze Etsy shop sales trends from historical data.
"""

import json
import os
from datetime import datetime
from collections import defaultdict


class SalesAnalyzer:
    """Analyze sales trends from tracked Etsy shop data."""

    def __init__(self, data_dir='data'):
        """
        Initialize the analyzer.

        Args:
            data_dir: Directory containing tracking data
        """
        self.data_dir = data_dir

    def load_history(self, shop_name):
        """
        Load historical data for a shop.

        Args:
            shop_name: Name of the shop

        Returns:
            List of historical entries
        """
        history_file = os.path.join(self.data_dir, f"{shop_name}_history.jsonl")

        if not os.path.exists(history_file):
            return []

        history = []
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    history.append(entry)
                except json.JSONDecodeError:
                    continue

        return history

    def compare_sales(self, shop_name, days_back=7):
        """
        Compare sales over the last N days.

        Args:
            shop_name: Name of the shop
            days_back: Number of days to analyze

        Returns:
            Dictionary with comparison data
        """
        history = self.load_history(shop_name)

        if not history:
            return None

        # Sort by timestamp
        history.sort(key=lambda x: x['timestamp'])

        # Get recent entries
        recent = history[-days_back:] if len(history) > days_back else history

        comparison = {
            'shop_name': shop_name,
            'days_analyzed': len(recent),
            'entries': []
        }

        for entry in recent:
            comparison['entries'].append({
                'timestamp': entry['timestamp'],
                'total_sales': entry.get('total_sales'),
                'products_count': len(entry.get('products', []))
            })

        # Calculate changes
        if len(comparison['entries']) >= 2:
            first = comparison['entries'][0]
            last = comparison['entries'][-1]

            if first['total_sales'] and last['total_sales']:
                sales_change = last['total_sales'] - first['total_sales']
                comparison['sales_change'] = sales_change
                comparison['sales_change_pct'] = (
                    (sales_change / first['total_sales']) * 100
                    if first['total_sales'] > 0 else 0
                )

        return comparison

    def find_top_products(self, shop_name, limit=10):
        """
        Find top-selling products from the latest data.

        Args:
            shop_name: Name of the shop
            limit: Number of top products to return

        Returns:
            List of top products
        """
        history = self.load_history(shop_name)

        if not history:
            return []

        # Get most recent entry with products
        latest = None
        for entry in reversed(history):
            if entry.get('products'):
                latest = entry
                break

        if not latest:
            return []

        products = latest['products']

        # Sort by sales
        products.sort(key=lambda p: p.get('sales') or 0, reverse=True)

        return products[:limit]

    def track_product_changes(self, shop_name, product_title):
        """
        Track how a specific product's sales have changed over time.

        Args:
            shop_name: Name of the shop
            product_title: Title of the product to track

        Returns:
            List of sales data points for the product
        """
        history = self.load_history(shop_name)

        product_history = []

        for entry in history:
            for product in entry.get('products', []):
                if product.get('title') == product_title:
                    product_history.append({
                        'timestamp': entry['timestamp'],
                        'sales': product.get('sales'),
                        'price': product.get('price')
                    })
                    break

        return product_history

    def generate_report(self, shop_name):
        """
        Generate a comprehensive report for a shop.

        Args:
            shop_name: Name of the shop

        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append(f"SALES REPORT: {shop_name}")
        report_lines.append("=" * 70)

        # Sales comparison
        comparison = self.compare_sales(shop_name, days_back=7)

        if comparison:
            report_lines.append(f"\nLast {comparison['days_analyzed']} tracking entries:")

            for entry in comparison['entries']:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                date_str = timestamp.strftime('%Y-%m-%d %H:%M')
                sales = entry['total_sales']
                sales_str = f"{sales:,}" if sales is not None else "N/A"
                report_lines.append(f"  {date_str}: {sales_str} total sales")

            if 'sales_change' in comparison:
                change = comparison['sales_change']
                pct = comparison['sales_change_pct']
                sign = "+" if change > 0 else ""
                report_lines.append(f"\nChange: {sign}{change:,} ({sign}{pct:.2f}%)")

        # Top products
        report_lines.append("\n" + "-" * 70)
        report_lines.append("TOP 10 PRODUCTS")
        report_lines.append("-" * 70)

        top_products = self.find_top_products(shop_name, limit=10)

        if top_products:
            for i, product in enumerate(top_products, 1):
                title = product.get('title', 'Unknown')
                sales = product.get('sales', 0)
                price = product.get('price', 'N/A')

                # Truncate long titles
                if len(title) > 50:
                    title = title[:47] + "..."

                report_lines.append(f"{i:2d}. {title}")
                report_lines.append(f"    Sales: {sales or 'N/A':>6} | Price: {price}")
        else:
            report_lines.append("No product data available")

        report_lines.append("\n" + "=" * 70)

        return "\n".join(report_lines)


def main():
    """Main function to run the analyzer."""
    analyzer = SalesAnalyzer()

    # Get all shop names from data directory
    shop_names = set()

    if os.path.exists('data'):
        for filename in os.listdir('data'):
            if filename.endswith('_history.jsonl'):
                shop_name = filename.replace('_history.jsonl', '')
                shop_names.add(shop_name)

    if not shop_names:
        print("No historical data found. Run etsy_tracker.py first.")
        return

    print("\nAvailable shops:")
    shop_list = sorted(shop_names)
    for i, shop in enumerate(shop_list, 1):
        print(f"{i}. {shop}")

    print("\nGenerating reports...\n")

    # Generate reports for all shops
    for shop_name in shop_list:
        report = analyzer.generate_report(shop_name)
        print(report)
        print()


if __name__ == '__main__':
    main()
