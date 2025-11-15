# 🛍️ Etsy Sales Tracker

A comprehensive analytics platform for tracking Etsy shops and products, similar to InsightFactory. Track sales trends, analyze keywords, monitor competitors, and discover emerging opportunities in the Etsy marketplace.

## ✨ Features

### 🏪 Shop Tracking
- Track multiple Etsy shops simultaneously
- Monitor total sales, listings count, and shop metrics
- Automated daily scraping with customizable schedules
- Shop comparison and competitive analysis

### 📊 Sales Analytics
- **7-Day Sales Tracking**: Monitor recent sales performance
- **Sales Velocity**: Identify products with accelerating sales
- **Historical Trends**: Track performance over time with snapshots
- **Top Performers**: Discover best-selling products

### 🔍 Keyword Intelligence
- **Tag Analysis**: Identify most popular keywords and tags
- **Emerging Keywords**: Detect tags gaining popularity
- **Tag Co-occurrence**: Understand keyword relationships
- **Search by Tag**: Find all listings using specific keywords

### 📈 Interactive Dashboard
- Built with Streamlit for a modern, responsive UI
- Interactive charts and visualizations using Plotly
- Real-time data exploration and filtering
- Export data to CSV for further analysis

### 🤖 Automation
- Scheduled scraping jobs using APScheduler
- Daily automated data collection
- Auto-discovery of popular shops
- Background processing with rate limiting

### 💾 Data Management
- SQLite database for persistent storage
- Historical snapshot tracking
- Efficient querying and indexing
- Data export capabilities

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd esales
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure settings**
Edit `config.yaml` to customize:
- Scraping delays and workers
- Scheduling intervals
- Shops to track
- Database location

### Usage

#### Option 1: Interactive Dashboard (Recommended)

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

**Dashboard Features:**
- **Dashboard**: Overview of all tracked shops and top performers
- **Shop Tracker**: Add/remove shops, trigger manual scrapes
- **Product Analysis**: Analyze listings with filters and charts
- **Keyword Intelligence**: Explore trending tags and keywords
- **Settings**: View scheduler status and system info

#### Option 2: Automated Scheduler

Run the background scheduler for automated scraping:

```bash
python scheduler.py
```

This will:
- Scrape all tracked shops daily at configured time (default: 2 AM)
- Optionally discover new popular shops weekly
- Store snapshots for trend analysis

#### Option 3: GitHub Actions (Recommended for Streamlit Cloud)

Trigger re-scraping directly from GitHub's interface:

1. Go to **Actions** tab in your GitHub repository
2. Select **"Re-scrape Etsy Shops"** workflow
3. Click **"Run workflow"**
4. Configure options and start

**Perfect for:**
- Streamlit Cloud deployments (can't run scripts locally)
- Fixing shops showing 0 sales
- Scheduled automatic updates

[📖 Full GitHub Actions Guide](.github/GITHUB_ACTIONS.md)

#### Option 4: Manual Scraping

Use the scraper programmatically:

```python
from scraper import EtsyScraper
from database import Database

# Initialize
scraper = EtsyScraper(delay=2.0)
db = Database()

# Scrape a shop
shop_info = scraper.scrape_shop("ExampleShop")
listings = scraper.scrape_shop_listings("ExampleShop")

# Store in database
db.add_shop(
    shop_name=shop_info['shop_name'],
    total_sales=shop_info['total_sales'],
    num_listings=shop_info['num_listings']
)

for listing in listings:
    db.add_listing(
        listing_id=listing['listing_id'],
        shop_name=listing['shop_name'],
        title=listing['title'],
        price=listing['price'],
        tags=listing['tags']
    )
    db.add_snapshot(
        listing_id=listing['listing_id'],
        sales_count=listing['sales_count']
    )

scraper.close()
db.close()
```

## 📁 Project Structure

```
esales/
├── scraper.py              # Original basic scraper (legacy)
├── database.py             # Database layer with SQLite
├── scheduler.py            # Automated scheduling system
├── app.py                  # Streamlit dashboard
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── scraper/               # Enhanced scraper module
│   ├── __init__.py
│   ├── core.py           # Main scraper orchestration
│   ├── etsy_client.py    # HTTP client with rate limiting
│   └── extractors.py     # Data extraction functions
│
├── analytics/             # Analytics and insights
│   ├── __init__.py
│   └── insights.py       # Advanced analytics functions
│
├── data/                  # Data storage
│   └── etsy_sales.db     # SQLite database
│
└── logs/                  # Log files
    └── scraper.log       # Scraper logs
```

## 🔧 Configuration

Edit `config.yaml` to customize behavior:

```yaml
scraper:
  delay: 2.0              # Delay between requests (seconds)
  max_workers: 5          # Concurrent scraping threads
  max_retries: 3          # Retry attempts for failed requests

scheduling:
  daily_scrape_hour: 2    # Hour for daily scrape (0-23)
  daily_scrape_minute: 0  # Minute for daily scrape
  enable_continuous: false # Enable interval-based scraping
  interval_hours: 24      # Interval between scrapes

shops:
  tracked_shops:          # Shops to track
    - "ExampleShop1"
    - "ExampleShop2"
  auto_discover: false    # Auto-discover popular shops
  min_sales_threshold: 1000 # Minimum sales for auto-discovery
```

## 📊 Analytics Features

### Trending Products
Identify products with accelerating sales:

```python
from analytics import get_trending_products
from database import Database

db = Database()
trending = get_trending_products(db, lookback_days=7, min_sales=5)

for product in trending:
    print(f"{product['title']}: {product['acceleration']}x acceleration")
```

### Price Analysis
Analyze pricing strategies:

```python
from analytics import suggest_price_ranges

price_ranges = suggest_price_ranges(db, category_tag="jewelry")
print(f"Budget range: ${price_ranges['recommendations']['budget']}")
print(f"Premium range: ${price_ranges['recommendations']['premium']}")
```

### Competitive Analysis
Compare shops:

```python
from analytics import generate_competitive_analysis

analysis = generate_competitive_analysis(
    db,
    shop_name="YourShop",
    competitor_shops=["Competitor1", "Competitor2"]
)

print(f"Your sales vs avg: {analysis['sales_vs_avg']:.2f}x")
```

## 🎯 How It Works

### Data Collection Process

1. **Shop Discovery**: Identify shops to track (manual or auto-discovery)
2. **Scraping**: Extract shop and listing data from Etsy pages
3. **Storage**: Store data in SQLite database with timestamps
4. **Snapshots**: Regular snapshots enable trend tracking
5. **Analysis**: Calculate metrics like 7-day sales, velocity, etc.
6. **Insights**: Generate recommendations and identify opportunities

### Comparison to InsightFactory

Our implementation replicates key InsightFactory features:

| Feature | InsightFactory | Etsy Sales Tracker |
|---------|---------------|-------------------|
| Shop Tracking | ✅ Top 50,000 shops | ✅ Unlimited shops |
| 7-Day Sales | ✅ | ✅ |
| Historical Data | ✅ 48-hour initial | ✅ Continuous |
| Tag Analysis | ✅ | ✅ |
| Sales Velocity | ✅ | ✅ |
| Dashboard | ✅ Web-based | ✅ Streamlit |
| Automation | ✅ | ✅ Scheduling |
| Export | ✅ | ✅ CSV |
| Cost | 💰 Subscription | 🆓 Free & Open Source |

## ⚠️ Important Notes

### Rate Limiting
- Default 2-second delay between requests
- Respects Etsy's servers to avoid blocks
- Configurable delays and retry logic
- User-agent rotation for reliability

### Data Accuracy
- Scrapes publicly available data only
- Data freshness depends on scraping frequency
- Some metrics may have slight delays
- Etsy HTML changes may require updates

### Legal & Ethical Use
- For personal research and analysis only
- Respect Etsy's Terms of Service
- Do not use for commercial purposes without permission
- Be respectful of rate limits

## 🛠️ Development

### Adding New Features

1. **New Extractors**: Add to `scraper/extractors.py`
2. **New Analytics**: Add to `analytics/insights.py`
3. **Database Changes**: Update schema in `database.py`
4. **UI Components**: Modify `app.py`

### Running Tests

```bash
# Test database
python -c "from database import Database; db = Database('test.db'); print('DB OK')"

# Test scraper
python -c "from scraper import EtsyScraper; s = EtsyScraper(); print('Scraper OK')"

# Test scheduler
python scheduler.py
# Press Ctrl+C to stop
```

### Logging

Logs are written to:
- Console: INFO level
- File: `logs/scraper.log` (configurable)

Adjust logging level in `config.yaml`:
```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

## 📈 Use Cases

### For Etsy Sellers
- Monitor competitor pricing and strategies
- Discover trending keywords for your niche
- Optimize listing tags based on top performers
- Track market trends and seasonal patterns

### For Market Research
- Analyze Etsy marketplace trends
- Identify emerging product categories
- Study pricing strategies across shops
- Discover popular shops and products

### For Developers
- Learn web scraping techniques
- Understand data analytics pipelines
- Explore Streamlit dashboard development
- Study scheduling and automation

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional analytics functions
- More visualization options
- Performance optimizations
- Better error handling
- Unit tests

## 📝 License

This project is for educational purposes. Use responsibly and respect Etsy's Terms of Service.

## 🙏 Acknowledgments

- Inspired by InsightFactory's Etsy analytics
- Built with Python, BeautifulSoup, Streamlit, and Plotly
- Community-driven open source project

## 📞 Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review code comments
3. Open an issue on GitHub

---

**Note**: This tool functions properly as of November 2024. Etsy's website structure may change over time, requiring updates to the scraping logic.
