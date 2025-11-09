# Etsy Sales Tracker

A Python tool to track multiple Etsy stores' daily sales and product information. This tool allows you to monitor up to 10 (or more) Etsy shops, tracking their total sales, individual product listings, and sales changes over time.

## Features

- 🖥️ **Web Dashboard**: Easy-to-use Streamlit interface for managing stores and viewing data
- 🏪 **Track Multiple Stores**: Monitor up to 10 Etsy stores simultaneously
- 📊 **Daily Sales Tracking**: Record total shop sales each day
- 📦 **Product-Level Tracking**: Track individual products and their sales
- 💾 **Historical Data**: Store data with timestamps for trend analysis
- 📈 **Daily Reports**: Generate comparison reports to see changes
- 🤖 **Automated Tracking**: GitHub Actions workflow runs daily at 7 AM EST
- ⚙️ **Configurable**: Easy JSON configuration for adding/removing stores

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd esales
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `stores.json` to configure which Etsy stores to track:

```json
{
  "stores": [
    {
      "name": "My Favorite Store",
      "shop_name": "ThePrintedPeanut",
      "url": "https://www.etsy.com/shop/ThePrintedPeanut",
      "enabled": true
    }
  ]
}
```

**Fields:**
- `name`: A friendly name for the store
- `shop_name`: The Etsy shop name (must match the URL)
- `url`: Full URL to the shop
- `enabled`: Set to `false` to temporarily disable tracking

## Usage

### Web Dashboard (Recommended for Beginners)

The easiest way to use the tracker is through the Streamlit web dashboard:

```bash
streamlit run app.py
```

This will open a web interface in your browser with three tabs:

**Tab 1: Manage Stores**
- Add new Etsy stores by URL
- Enable/disable tracking for specific stores
- Delete stores from tracking
- Manually refresh data

**Tab 2: Sales Overview**
- View total sales for all stores in a table
- See when each store was last updated
- Download sales data as CSV
- View summary metrics

**Tab 3: Top Products**
- See the top-selling product for each store
- View top 5 products per store
- Compare product performance

The dashboard automatically loads the latest tracked data and provides an intuitive interface for managing your stores.

### Basic Tracking (Command Line)

Run the tracker to collect data from all enabled stores:

```bash
python etsy_tracker.py
```

This will:
1. Scrape each enabled store
2. Collect total sales information
3. Fetch product listings (up to 3 pages per store)
4. Save data to the `data/` directory
5. Display a summary report

### Using as a Library

```python
from etsy_tracker import EtsyShopTracker

# Initialize tracker
tracker = EtsyShopTracker()

# Track all stores
results = tracker.track_all_stores(track_products=True)

# Track a specific store
store_config = {
    "name": "Example Store",
    "shop_name": "ExampleShop",
    "url": "https://www.etsy.com/shop/ExampleShop",
    "enabled": true
}
result = tracker.track_store(store_config, track_products=True)

# Generate daily report
report = tracker.get_daily_report()
print(f"Tracked {len(report['stores'])} stores")
```

### Data Storage

Data is saved in two formats:

1. **Daily Snapshots**: `data/{shop_name}_YYYYMMDD.json`
   - Contains complete data for that day
   - Easy to review individual days

2. **Historical Log**: `data/{shop_name}_history.jsonl`
   - Line-delimited JSON with all historical data
   - One entry per tracking run
   - Useful for trend analysis

### Example Data Structure

```json
{
  "url": "https://www.etsy.com/shop/ExampleShop",
  "timestamp": "2025-11-09T10:30:00.123456",
  "total_sales": 15234,
  "products": [
    {
      "listing_id": "123456789",
      "url": "https://www.etsy.com/listing/123456789",
      "title": "Handmade Widget",
      "price": "$29.99",
      "sales": 456,
      "timestamp": "2025-11-09T10:30:05.123456"
    }
  ],
  "error": null
}
```

## Automated Daily Tracking

### Using GitHub Actions (Recommended)

The repository includes a GitHub Actions workflow that automatically runs the tracker daily at 7 AM EST.

**Features:**
- Runs automatically every day at 7 AM EST
- Commits data back to the repository
- No server setup required
- Stores artifacts as backup (30-day retention)
- Can be manually triggered from the Actions tab

**Setup:**
1. The workflow is already configured in `.github/workflows/daily-tracker.yml`
2. Push your changes to GitHub
3. The workflow will run automatically daily
4. View results in the "Actions" tab on GitHub

**Manual Trigger:**
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Daily Etsy Sales Tracker"
4. Click "Run workflow"

**View Results:**
- Check the `data/` directory in your repository for daily snapshots
- Download artifacts from the Actions run for backups
- View execution summary in each workflow run

### Using Cron (Linux/Mac)

Add to your crontab to run daily at 9 AM:

```bash
crontab -e
```

Add this line:
```
0 9 * * * cd /path/to/esales && python etsy_tracker.py >> logs/tracker.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a new task
3. Set trigger to run daily
4. Set action to run:
   - Program: `python`
   - Arguments: `C:\path\to\esales\etsy_tracker.py`
   - Start in: `C:\path\to\esales`

## Analyzing Data

### View Historical Trends

You can parse the JSONL history files to analyze trends:

```python
import json

# Read historical data
with open('data/ShopName_history.jsonl', 'r') as f:
    history = [json.loads(line) for line in f]

# Analyze sales growth
for entry in history:
    print(f"{entry['timestamp']}: {entry['total_sales']} sales")
```

### Compare Products

Track which products are selling:

```python
# Load today's data
with open('data/ShopName_20251109.json', 'r') as f:
    data = json.load(f)

# Sort products by sales
products = sorted(data['products'], key=lambda p: p['sales'] or 0, reverse=True)

print("Top 5 products:")
for product in products[:5]:
    print(f"{product['title']}: {product['sales']} sales")
```

## Legacy Scraper

The original `scraper.py` is still available for basic listing scraping:

```python
from scraper import get_listing_info

# Scrape listings from any Etsy page
get_listing_info("https://www.etsy.com/c/home-and-living")
```

## Important Notes

- **Rate Limiting**: The tracker includes delays between requests to be respectful of Etsy's servers
- **Data Accuracy**: Sales counts are scraped from public pages and may not always be available
- **Terms of Service**: Ensure your use complies with Etsy's Terms of Service
- **Etsy Changes**: If Etsy updates their website structure, the scraper may need updates

## Troubleshooting

**No sales data retrieved:**
- Etsy may have changed their HTML structure
- Try increasing delays between requests
- Check if the shop URL is correct

**Products not found:**
- The shop may have few products
- Try increasing `max_pages` parameter
- Some shops may have private listings

**Request errors:**
- Check your internet connection
- Etsy may be temporarily blocking requests (increase delays)
- Verify URLs are correct

## Future Enhancements

Potential improvements:
- Email notifications for sales milestones
- Web dashboard for visualizing trends
- Export to CSV/Excel
- Price change tracking
- Competitor analysis
- Sales velocity calculations

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes. Please ensure your use complies with Etsy's Terms of Service and robots.txt.

---

**Last Updated**: November 2025
