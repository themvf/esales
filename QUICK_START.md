# 🚀 Quick Start: Fix "0 Sales" Issue

Your shops are showing 0 sales because Etsy's HTML changed since 2023. Here's how to fix it **in 2 minutes**:

## ✅ Using GitHub Actions (Easiest - No Code Required)

### Step 1: Enable Workflow Permissions

1. Go to your GitHub repository
2. Click **Settings** → **Actions** → **General**
3. Scroll to "Workflow permissions"
4. Select ✅ **"Read and write permissions"**
5. Click **Save**

### Step 2: Run the Re-scrape Workflow

1. Go to the **Actions** tab in your repository
   - URL: `https://github.com/YOUR_USERNAME/esales/actions`

2. Click **"Re-scrape Etsy Shops"** in the left sidebar

3. Click **"Run workflow"** (green button, top right)

4. **Configure settings** (or use defaults):
   ```
   Max listings to scrape per shop: 50
   Specific shops: [leave empty for all shops]
   ```

5. Click **"Run workflow"** to start

### Step 3: Monitor Progress

- Watch the workflow run (takes 5-15 minutes)
- Green checkmark = Success ✅
- Click the run to see detailed logs

### Step 4: View Updated Data

1. **Wait 2-3 minutes** for Streamlit Cloud to redeploy
2. **Refresh your dashboard** (hard refresh: Ctrl+F5)
3. **Check sales numbers** - Should now show actual sales! 🎉

## 🎯 What Happens

```
GitHub Action runs
    ↓
Scrapes all shops with improved extractors
    ↓
Finds sales data using JSON-LD + meta tags + HTML
    ↓
Updates database file (data/etsy_sales.db)
    ↓
Commits and pushes database
    ↓
Streamlit Cloud auto-deploys
    ↓
Your dashboard shows real sales! ✅
```

## 📊 Expected Results

**Before:**
```
Shop: CoolShop
Sales: 0
Listings: 0
```

**After:**
```
Shop: CoolShop
Sales: 12,450
Listings: 234
```

## ⚙️ Advanced Options

### Scrape Specific Shops Only

Instead of all shops, scrape just one or two:

```
Max listings: 50
Specific shops: ShopName1,ShopName2
```

### Scrape More Listings

To get more listings per shop (slower but more complete):

```
Max listings: 100
Specific shops: [empty]
```

### Schedule Automatic Updates

Edit `.github/workflows/rescrape-shops.yml`:

```yaml
on:
  workflow_dispatch:
    # ... existing inputs ...

  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
```

Commit and push this change to enable weekly auto-updates.

## 🛠️ Alternative: Run Locally

If you prefer running on your computer:

```bash
# Pull latest code
git pull origin claude/analyze-insightfactory-scraping-01AnWmBerEwY1aa3oCwcwBoC

# Install dependencies
pip install -r requirements.txt

# Run re-scrape
python rescrape_shops.py

# Push updated database
git add data/etsy_sales.db
git commit -m "Update sales data"
git push
```

## ❓ Troubleshooting

### Action fails with "Permission denied"

**Fix:** Enable workflow write permissions (see Step 1 above)

### Shops still show 0 sales after running

**Possible reasons:**
1. Shop name is misspelled
2. Shop is private/on vacation
3. Etsy is blocking requests

**Fix:**
- Check workflow logs for errors
- Try scraping one shop: `--shops "ExactShopName"`
- Wait a few hours and try again

### Database not updating in Streamlit

**Fix:**
1. Check if commit was created in GitHub
2. Wait 2-3 minutes for Streamlit to redeploy
3. Hard refresh browser (Ctrl+F5)
4. Check "Manage app" for deployment status

## 🎉 Success Indicators

You'll know it worked when:

✅ Workflow shows green checkmark
✅ New commit appears: "Update Etsy sales data [automated]"
✅ Streamlit Cloud shows "Deploying..."
✅ Dashboard refreshes with real sales numbers
✅ 7-day sales start appearing (after 7 days of data)

## 📚 More Information

- [Full GitHub Actions Guide](.github/GITHUB_ACTIONS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Complete README](README.md)

---

**Need help?** Check the workflow logs in the Actions tab - they show exactly what was scraped and any errors encountered.
