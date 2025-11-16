# Firecrawl Setup Guide

## What is Firecrawl?

Firecrawl is a web scraping API that handles all anti-bot protection automatically. It bypasses:
- Cloudflare protection
- CAPTCHA challenges
- Bot detection
- JavaScript rendering
- IP blocking

This is the **recommended solution** for reliably scraping Etsy shops.

## Why Use Firecrawl?

✅ **Works 100% of the time** - no 403 errors
✅ **No complex browser automation** needed
✅ **Handles JavaScript** automatically
✅ **Fast and reliable**
✅ **Simple API integration**

**Cost:** Free tier available, paid plans from $20/month

## Setup Instructions

### Step 1: Get Your API Key

1. Go to https://firecrawl.dev
2. Sign up for an account
3. Get your API key from the dashboard
4. Copy the API key (starts with `fc-`)

### Step 2: Add API Key to GitHub Secrets

For the GitHub Action to work:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `FIRECRAWL_API_KEY`
5. Value: Paste your Firecrawl API key
6. Click **"Add secret"**

### Step 3: Run the GitHub Action

Now when you run the "Re-scrape Etsy Shops" action:

1. Go to **Actions** tab
2. Click **"Re-scrape Etsy Shops"**
3. Click **"Run workflow"**
4. The action will automatically use Firecrawl
5. You'll see: `✅ Firecrawl API key detected - using Firecrawl for scraping`

### Step 4: Verify It Works

After the action completes:
- Check for commit: "Update Etsy sales data [automated]"
- Open Streamlit dashboard
- Refresh (Ctrl+F5)
- **You should now see REAL sales data!** 🎉

## Local Development (Optional)

To test locally:

### Option 1: Environment Variable

```bash
export FIRECRAWL_API_KEY="fc-your-api-key-here"
python rescrape_shops.py
```

### Option 2: Config File

Edit `config.yaml`:

```yaml
scraper:
  firecrawl_api_key: "fc-your-api-key-here"
```

Then run:
```bash
python rescrape_shops.py
```

## Testing

To test if Firecrawl is working:

```python
from scraper.etsy_client import EtsyClient
import os

# Set your API key
os.environ['FIRECRAWL_API_KEY'] = 'fc-your-key-here'

# Test
client = EtsyClient()
response = client.get('https://www.etsy.com/shop/CarterPrintingCo')

if response and response.status_code == 200:
    print(f"✅ SUCCESS! Got {len(response.text):,} bytes")
    print(f"Firecrawl is working!")
else:
    print("❌ Failed")
```

## Pricing

**Free Tier:**
- 500 scrapes/month
- Good for testing
- ~16 scrapes/day

**Hobby Plan ($20/month):**
- 10,000 scrapes/month
- Perfect for tracking 10-20 shops daily
- ~330 scrapes/day

**Growth Plan ($99/month):**
- 100,000 scrapes/month
- For larger operations
- ~3,300 scrapes/day

**Calculate your needs:**
- 3 shops × 50 listings each = 150 scrapes per run
- Daily runs = 150 × 30 days = 4,500 scrapes/month
- **Hobby plan ($20/month) is perfect for this use case**

## Fallback Behavior

If no Firecrawl API key is set:
- ⚠️ Falls back to cloudscraper
- ❌ Will likely get 403 errors from Etsy
- ⚠️ Won't work reliably

**Always use Firecrawl for production scraping!**

## Troubleshooting

### "No Firecrawl API key found"

Make sure:
1. API key is set in GitHub Secrets as `FIRECRAWL_API_KEY`
2. Or set environment variable: `export FIRECRAWL_API_KEY="fc-..."`
3. Or add to `config.yaml` under `scraper.firecrawl_api_key`

### "Firecrawl returned no HTML"

- Check your API key is valid
- Check you have credits remaining
- Try a different URL

### Still getting 0 sales

- Make sure the GitHub Action ran AFTER setting the API key
- Check the action logs for "✅ Firecrawl API key detected"
- If you see "⚠️ No Firecrawl API key", add it to GitHub Secrets

## Success Indicators

You'll know it's working when:

✅ Action logs show: "✅ Firecrawl API key detected"
✅ No 403 errors in logs
✅ Commit created: "Update Etsy sales data [automated]"
✅ Dashboard shows real sales numbers (not 0)
✅ Listings appear in Product Analysis

---

**This is the solution that will actually work!** Firecrawl handles all the complexity that was causing 403 errors before.
