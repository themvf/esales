# Troubleshooting Guide

## Problem: Shops showing 0 sales

If you've added shops to the tracker but they're showing 0 sales despite having thousands of sales on Etsy, this is likely because:

1. **Etsy's HTML structure has changed** - The original extractors from 2023 may not work with current Etsy pages
2. **The shops haven't been properly scraped yet** - They were added to the database but not fully scraped

### Solution 1: Re-scrape with Improved Extractors (Recommended)

We've created improved extractors that use multiple methods to extract data:
- JSON-LD structured data (most reliable)
- Meta tags (og:price, og:title, etc.)
- Multiple HTML parsing patterns

**Run the re-scrape script:**

```bash
python rescrape_shops.py
```

This will:
- Re-scrape all shops in your database
- Use improved extraction methods
- Update sales counts, listings, and all data
- Scrape up to 50 listings per shop

**Expected output:**
```
Starting re-scrape of all shops...
Found 3 shops to re-scrape

[1/3] Processing: ExampleShop
----------------------------------------------------------
Re-scraping shop: ExampleShop
  Shop sales: 12,450
  Shop listings: 234
  Scraping 50 listings...
  Progress: 5/50 listings
  ...
✅ Successfully scraped 50/50 listings for ExampleShop
```

### Solution 2: Test Individual Shop

To test if a specific shop can be scraped correctly:

```bash
python test_scraper.py ShopName
```

Example:
```bash
python test_scraper.py TheClayPlay
```

This will:
- Show detailed debug output
- Display extracted shop info and sales
- Show first 3 listings
- Ask if you want to save to database

### Solution 3: Check Database Contents

To see what's currently in your database:

```bash
python test_scraper.py
```

(without shop name)

This shows:
- All tracked shops
- Sales counts in database
- Number of listings per shop
- Latest snapshot data

### Solution 4: Manual Scrape from Dashboard

In the Streamlit dashboard:

1. Go to **Shop Tracker** page
2. Find the shop with 0 sales
3. Click **"Scrape Now"** button
4. Wait for scraping to complete
5. Refresh the page

### Understanding the Issue

The original scraper looked for HTML patterns like:
- `<span class="wt-text-caption">1,234 sales</span>`
- Text matching `\d+ sales`

But Etsy may have changed to:
- Different CSS classes
- JavaScript-rendered content
- Different HTML structure

The improved extractors handle this by:
1. **First trying JSON-LD** - Structured data that rarely changes
2. **Then trying meta tags** - Standard og:price, og:title tags
3. **Finally trying HTML** - Multiple patterns and fallbacks

### After Re-scraping

Once you've re-scraped:

1. **Check the Dashboard** - Sales numbers should now be correct
2. **Wait 24 hours** - For 7-day sales trends to appear (need historical data)
3. **Set up scheduling** - Run daily scrapes to track trends

```python
# In config.yaml
scheduling:
  daily_scrape_hour: 2  # 2 AM daily
  enable_continuous: false
```

### Still Having Issues?

If re-scraping doesn't work:

1. **Check logs** - Look for error messages
2. **Test with a known shop** - Try a popular shop like "TheClayPlay"
3. **Verify internet connection** - Make sure you can access Etsy
4. **Check rate limiting** - Increase delay in config.yaml:

```yaml
scraper:
  delay: 3.0  # Increase from 2.0 to 3.0 seconds
```

### Technical Details

The improved extractors (`scraper/extractors_improved.py`) use:

```python
# Method 1: JSON-LD (most reliable)
json_ld = soup.find_all('script', type='application/ld+json')
# Extracts: title, price, description, image

# Method 2: Meta tags
og_price = soup.find('meta', property='og:price:amount')
# Extracts: price, currency, title, image

# Method 3: HTML patterns
# Multiple regex patterns for sales count
```

This multi-layered approach is much more robust than the original single-pattern matching.
