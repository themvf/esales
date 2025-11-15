"""
Data Extractors
Functions to extract data from Etsy HTML pages
"""

import re
import json
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_listing_ids(html: str) -> List[str]:
    """
    Extract listing IDs from an Etsy page

    Args:
        html: HTML content of the page

    Returns:
        List of listing IDs
    """
    soup = BeautifulSoup(html, "lxml")
    listing_ids = []

    # Find all anchor tags with data-listing-id attribute
    listings = soup.find_all("a", attrs={"data-listing-id": True})

    for tag in listings:
        listing_id = tag.get("data-listing-id")
        if listing_id and listing_id not in listing_ids:
            listing_ids.append(listing_id)

    logger.info(f"Extracted {len(listing_ids)} listing IDs")
    return listing_ids


def extract_shop_info(html: str, shop_name: str = None) -> Dict:
    """
    Extract shop information from an Etsy shop page

    Args:
        html: HTML content of the shop page
        shop_name: Shop name (optional, will try to extract if not provided)

    Returns:
        Dictionary with shop information
    """
    soup = BeautifulSoup(html, "lxml")
    shop_info = {}

    # Extract shop name from the page if not provided
    if not shop_name:
        # Try to find shop name in various places
        shop_link = soup.find('link', attrs={'rel': 'alternate', 'type': 'application/rss+xml'})
        if shop_link and shop_link.get('title'):
            match = re.search(r'Shop RSS for (\w+) on Etsy', shop_link.get('title'))
            if match:
                shop_name = match.group(1)

    shop_info['shop_name'] = shop_name

    # Extract total sales
    sales_text = soup.find(text=re.compile(r'\d+\s+sales?', re.IGNORECASE))
    if sales_text:
        match = re.search(r'(\d+(?:,\d+)*)', sales_text)
        if match:
            shop_info['total_sales'] = int(match.group(1).replace(',', ''))

    # Extract location
    location_span = soup.find('span', class_=re.compile(r'location', re.IGNORECASE))
    if location_span:
        shop_info['location'] = location_span.get_text(strip=True)

    # Extract number of listings (from shop page)
    listings_text = soup.find(text=re.compile(r'\d+\s+items?', re.IGNORECASE))
    if listings_text:
        match = re.search(r'(\d+(?:,\d+)*)', listings_text)
        if match:
            shop_info['num_listings'] = int(match.group(1).replace(',', ''))

    logger.debug(f"Extracted shop info: {shop_info}")
    return shop_info


def extract_listing_info(html: str, listing_id: str = None) -> Dict:
    """
    Extract listing information from an Etsy listing page

    Args:
        html: HTML content of the listing page
        listing_id: Listing ID (optional)

    Returns:
        Dictionary with listing information
    """
    soup = BeautifulSoup(html, "lxml")
    listing_info = {'listing_id': listing_id}

    # Extract title
    title_tag = soup.find('h1')
    if title_tag:
        listing_info['title'] = title_tag.get_text(strip=True)

    # Extract price
    price_tag = soup.find('p', class_=re.compile(r'price', re.IGNORECASE))
    if not price_tag:
        # Alternative: look for price in meta tags
        price_meta = soup.find('meta', {'property': 'og:price:amount'})
        if price_meta:
            listing_info['price'] = float(price_meta.get('content', 0))
            currency_meta = soup.find('meta', {'property': 'og:price:currency'})
            if currency_meta:
                listing_info['currency'] = currency_meta.get('content', 'USD')
    else:
        price_text = price_tag.get_text(strip=True)
        # Extract numeric value
        match = re.search(r'[\d,]+\.?\d*', price_text)
        if match:
            listing_info['price'] = float(match.group().replace(',', ''))
        # Extract currency
        currency_match = re.search(r'[A-Z]{3}', price_text)
        if currency_match:
            listing_info['currency'] = currency_match.group()

    # Extract sales count
    sales_regex = re.compile(r'\d+(?:,\d+)?\s+sales?', re.IGNORECASE)
    sales_span = soup.find('span', class_='wt-text-caption', text=sales_regex)
    if sales_span:
        sales_text = sales_span.get_text(strip=True)
        match = re.search(r'(\d+(?:,\d+)*)', sales_text)
        if match:
            listing_info['sales_count'] = int(match.group(1).replace(',', ''))

    # Extract shop name
    shop_link = soup.find('link', attrs={'rel': 'alternate', 'type': 'application/rss+xml'})
    if shop_link and shop_link.get('title'):
        match = re.search(r'Shop RSS for (\w+) on Etsy', shop_link.get('title'))
        if match:
            listing_info['shop_name'] = match.group(1)

    # Extract tags
    tags = extract_listing_tags(html)
    if tags:
        listing_info['tags'] = tags

    # Extract description
    description_div = soup.find('div', {'data-product-details-description': True})
    if description_div:
        listing_info['description'] = description_div.get_text(strip=True)[:500]  # Limit length

    # Extract image URL
    image_tag = soup.find('meta', {'property': 'og:image'})
    if image_tag:
        listing_info['image_url'] = image_tag.get('content')

    # Extract favorites/views if available
    favorites_text = soup.find(text=re.compile(r'\d+\s+favorites?', re.IGNORECASE))
    if favorites_text:
        match = re.search(r'(\d+(?:,\d+)*)', favorites_text)
        if match:
            listing_info['favorites'] = int(match.group(1).replace(',', ''))

    logger.debug(f"Extracted listing info for {listing_id}: {listing_info.get('title', 'Unknown')}")
    return listing_info


def extract_listing_tags(html: str) -> List[str]:
    """
    Extract tags/keywords from a listing page

    Args:
        html: HTML content of the listing page

    Returns:
        List of tags
    """
    soup = BeautifulSoup(html, "lxml")
    tags = []

    # Method 1: Look for tags in structured data (JSON-LD)
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'keywords' in data:
                keywords = data['keywords']
                if isinstance(keywords, str):
                    tags.extend([k.strip() for k in keywords.split(',')])
                elif isinstance(keywords, list):
                    tags.extend(keywords)
        except (json.JSONDecodeError, AttributeError):
            pass

    # Method 2: Look for tags in meta keywords
    meta_keywords = soup.find('meta', {'name': 'keywords'})
    if meta_keywords:
        keywords = meta_keywords.get('content', '')
        tags.extend([k.strip() for k in keywords.split(',')])

    # Method 3: Look for tags in specific sections (Etsy-specific)
    tag_links = soup.find_all('a', href=re.compile(r'/search/\?q='))
    for link in tag_links:
        tag_text = link.get_text(strip=True)
        if tag_text and len(tag_text) < 50:  # Reasonable tag length
            tags.append(tag_text)

    # Remove duplicates and clean
    tags = list(set([tag.strip() for tag in tags if tag.strip()]))

    logger.debug(f"Extracted {len(tags)} tags")
    return tags


def extract_shop_url_from_listing(html: str) -> Optional[str]:
    """
    Extract shop URL from a listing page

    Args:
        html: HTML content of the listing page

    Returns:
        Shop URL or None
    """
    soup = BeautifulSoup(html, "lxml")

    # Look for shop link
    shop_link = soup.find('a', href=re.compile(r'/shop/'))
    if shop_link:
        href = shop_link.get('href')
        if href.startswith('http'):
            return href
        else:
            return f"https://www.etsy.com{href}"

    return None
