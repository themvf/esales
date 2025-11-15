"""
Improved Data Extractors for Etsy (2024)
Uses JSON-LD structured data and more robust selectors
"""

import re
import json
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_json_ld(html: str) -> List[Dict]:
    """Extract all JSON-LD structured data from page"""
    soup = BeautifulSoup(html, "lxml")
    json_ld_scripts = soup.find_all('script', type='application/ld+json')

    results = []
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            results.append(data)
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    return results


def extract_listing_info_improved(html: str, listing_id: str = None) -> Dict:
    """
    Extract listing information using multiple methods
    Priority: JSON-LD > Meta tags > HTML parsing
    """
    soup = BeautifulSoup(html, "lxml")
    listing_info = {'listing_id': listing_id}

    # Method 1: Try JSON-LD structured data
    json_ld_data = extract_json_ld(html)
    for data in json_ld_data:
        if isinstance(data, dict):
            # Product schema
            if data.get('@type') == 'Product':
                listing_info['title'] = data.get('name')

                # Offers/price
                offers = data.get('offers', {})
                if isinstance(offers, dict):
                    listing_info['price'] = float(offers.get('price', 0))
                    listing_info['currency'] = offers.get('priceCurrency', 'USD')

                # Description
                if 'description' in data:
                    listing_info['description'] = data['description'][:500]

                # Image
                if 'image' in data:
                    img = data['image']
                    if isinstance(img, list) and img:
                        listing_info['image_url'] = img[0]
                    elif isinstance(img, str):
                        listing_info['image_url'] = img

    # Method 2: Meta tags (very reliable)
    if 'title' not in listing_info:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            listing_info['title'] = og_title.get('content')

    if 'price' not in listing_info:
        price_meta = soup.find('meta', property='og:price:amount')
        if price_meta:
            try:
                listing_info['price'] = float(price_meta.get('content', 0))
            except (ValueError, TypeError):
                pass

        currency_meta = soup.find('meta', property='og:price:currency')
        if currency_meta:
            listing_info['currency'] = currency_meta.get('content', 'USD')

    if 'image_url' not in listing_info:
        og_image = soup.find('meta', property='og:image')
        if og_image:
            listing_info['image_url'] = og_image.get('content')

    # Method 3: HTML parsing for sales count (Etsy-specific)
    # Try multiple patterns as Etsy changes their HTML
    sales_patterns = [
        (re.compile(r'(\d+(?:,\d+)*)\s+sales?', re.IGNORECASE), 1),
        (re.compile(r'sales?:\s*(\d+(?:,\d+)*)', re.IGNORECASE), 1),
    ]

    # Look in all text content
    page_text = soup.get_text()
    for pattern, group in sales_patterns:
        match = pattern.search(page_text)
        if match:
            try:
                listing_info['sales_count'] = int(match.group(group).replace(',', ''))
                break
            except (ValueError, IndexError):
                continue

    # Also try specific elements
    if 'sales_count' not in listing_info:
        # Look for sales in spans, divs, etc.
        for elem in soup.find_all(['span', 'div', 'p']):
            text = elem.get_text(strip=True)
            if 'sale' in text.lower():
                match = re.search(r'(\d+(?:,\d+)*)', text)
                if match:
                    try:
                        listing_info['sales_count'] = int(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        continue

    # Extract shop name from URL or meta
    if 'shop_name' not in listing_info:
        # Try from canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            url = canonical.get('href', '')
            # Etsy URLs: /shop/ShopName or /listing/123/product?ref=shop_home
            match = re.search(r'/shop/([^/]+)', url)
            if match:
                listing_info['shop_name'] = match.group(1)

    # Extract tags - look for keyword meta tag
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords:
        keywords = meta_keywords.get('content', '')
        if keywords:
            listing_info['tags'] = [k.strip() for k in keywords.split(',') if k.strip()]

    logger.debug(f"Extracted listing info: {listing_info}")
    return listing_info


def extract_shop_info_improved(html: str, shop_name: str = None) -> Dict:
    """
    Extract shop information using multiple methods
    """
    soup = BeautifulSoup(html, "lxml")
    shop_info = {'shop_name': shop_name}

    # Try JSON-LD first
    json_ld_data = extract_json_ld(html)
    for data in json_ld_data:
        if isinstance(data, dict) and data.get('@type') in ['Store', 'Organization']:
            if 'name' in data:
                shop_info['shop_name'] = data['name']
            if 'location' in data:
                loc = data['location']
                if isinstance(loc, dict):
                    shop_info['location'] = loc.get('address', {}).get('addressCountry')

    # Look for sales count in page text
    page_text = soup.get_text()

    # Multiple patterns for sales
    sales_patterns = [
        r'(\d+(?:,\d+)*)\s+sales',
        r'sales:\s*(\d+(?:,\d+)*)',
        r'(\d+(?:,\d+)*)\s+total\s+sales',
    ]

    for pattern in sales_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            try:
                shop_info['total_sales'] = int(match.group(1).replace(',', ''))
                break
            except (ValueError, IndexError):
                continue

    # Look for items/listings count
    items_patterns = [
        r'(\d+(?:,\d+)*)\s+items?',
        r'(\d+(?:,\d+)*)\s+listings?',
    ]

    for pattern in items_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            try:
                shop_info['num_listings'] = int(match.group(1).replace(',', ''))
                break
            except (ValueError, IndexError):
                continue

    logger.debug(f"Extracted shop info: {shop_info}")
    return shop_info


def extract_listing_ids_improved(html: str) -> List[str]:
    """
    Extract listing IDs using multiple methods
    """
    soup = BeautifulSoup(html, "lxml")
    listing_ids = set()

    # Method 1: data-listing-id attribute
    for tag in soup.find_all(attrs={'data-listing-id': True}):
        lid = tag.get('data-listing-id')
        if lid:
            listing_ids.add(str(lid))

    # Method 2: Links to /listing/ID
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        match = re.search(r'/listing/(\d+)', href)
        if match:
            listing_ids.add(match.group(1))

    # Method 3: JSON data
    json_scripts = soup.find_all('script', type='application/json')
    for script in json_scripts:
        try:
            # Look for listing IDs in JSON
            matches = re.findall(r'"listing_id"\s*:\s*(\d+)', script.string or '')
            listing_ids.update(matches)
        except:
            continue

    result = list(listing_ids)
    logger.info(f"Extracted {len(result)} listing IDs")
    return result
