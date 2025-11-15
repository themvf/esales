# GitHub Actions Guide

## Re-scrape Etsy Shops Action

This GitHub Action allows you to re-scrape your tracked Etsy shops directly from GitHub's interface, updating the database with current sales data.

### Why Use This?

- **Fix 0 sales issues** - Re-scrape shops that show 0 sales despite having real sales
- **Update data** - Refresh sales counts and listings for all shops
- **No local setup needed** - Run from GitHub's web interface
- **Automatic sync** - Database updates automatically sync to Streamlit Cloud

### How to Use

#### Method 1: Manual Trigger (Recommended)

1. **Go to the Actions tab** in your GitHub repository
   - URL: `https://github.com/USERNAME/esales/actions`

2. **Click on "Re-scrape Etsy Shops"** workflow in the left sidebar

3. **Click "Run workflow"** button (top right)

4. **Configure options** (optional):
   - **Max listings**: Number of listings to scrape per shop (default: 50)
   - **Specific shops**: Comma-separated shop names to scrape (leave empty for all)

   Examples:
   - Scrape all shops: Leave "Specific shops" empty
   - Scrape 2 shops: Enter `ShopName1,ShopName2`
   - Scrape 100 listings per shop: Set "Max listings" to `100`

5. **Click green "Run workflow" button** to start

6. **Monitor progress**:
   - Click on the running workflow to see live logs
   - Wait for completion (typically 5-15 minutes depending on shop count)

7. **Check results**:
   - Database will be automatically committed and pushed
   - Streamlit Cloud will redeploy with new data (takes ~2 minutes)
   - Refresh your dashboard to see updated sales numbers

#### Method 2: Scheduled Automatic Runs (Optional)

To enable automatic weekly scraping:

1. Edit `.github/workflows/rescrape-shops.yml`
2. Uncomment the schedule section:

```yaml
on:
  workflow_dispatch:
    # ... inputs ...

  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
```

3. Commit and push the change

### What the Action Does

1. ✅ Checks out your repository
2. ✅ Installs Python and dependencies
3. ✅ Runs the improved scraper on all/specific shops
4. ✅ Uses JSON-LD, meta tags, and HTML parsing for robust extraction
5. ✅ Updates the SQLite database with fresh data
6. ✅ Commits and pushes the updated database
7. ✅ Uploads logs as artifacts for debugging

### Workflow Outputs

**Success:**
```
Re-scrape Complete! 🎉

Details:
- Timestamp: 2024-11-15 14:30:00 UTC
- Max listings: 50
- Shops: All shops in database

Database has been updated and pushed to the repository.
Streamlit Cloud will automatically redeploy with the new data.
```

**Logs:**
- Available under "Artifacts" section of the workflow run
- Kept for 7 days
- Useful for debugging scraping issues

### Troubleshooting

#### Action fails with "Permission denied"

**Solution:** Enable workflow write permissions:

1. Go to Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Click "Save"

#### No shops in database

**Error:** `No shops in database to re-scrape`

**Solution:**
- Add shops through the Streamlit dashboard first
- Or commit an initial database file with shops

#### Some shops still show 0 sales

**Possible causes:**
1. **Shop doesn't exist** - Verify shop name is correct
2. **Etsy blocking** - Rate limits exceeded (increase delay in config)
3. **Private shop** - Shop may be on vacation or private

**Solution:**
- Check the workflow logs for specific errors
- Try scraping individual shop: `--shops "ShopName"`
- Increase scraper delay in `config.yaml`

#### Database not updating in Streamlit

**Solution:**
1. Wait 2-3 minutes for Streamlit Cloud to redeploy
2. Hard refresh your browser (Ctrl+F5)
3. Check if commit was successful in repository

### Advanced Usage

#### Command-Line (Local)

You can also run the script locally with the same options:

```bash
# Scrape all shops
python rescrape_shops.py

# Scrape with custom max listings
python rescrape_shops.py --max-listings 100

# Scrape specific shops
python rescrape_shops.py --shops "Shop1,Shop2,Shop3"

# Combine options
python rescrape_shops.py --max-listings 25 --shops "MyShop"
```

#### Modify Workflow

You can customize the workflow by editing `.github/workflows/rescrape-shops.yml`:

**Change default max listings:**
```yaml
max_listings:
  description: 'Max listings to scrape per shop'
  default: '100'  # Changed from 50
```

**Add more input options:**
```yaml
delay:
  description: 'Delay between requests (seconds)'
  default: '2.0'
  type: string
```

**Change commit message:**
```yaml
git commit -m "Your custom message here"
```

### Best Practices

1. **Start small**: First run with `--max-listings 10` to test
2. **Monitor rate limits**: Don't scrape too frequently (max once per day)
3. **Check logs**: Always review artifacts if something fails
4. **Specific shops**: Use `--shops` to re-scrape only problematic shops
5. **Schedule wisely**: If using cron, run during low-traffic hours (2-4 AM)

### Example Workflows

**Fix one shop showing 0 sales:**
```
Inputs:
- Max listings: 50
- Specific shops: TheProblematicShop
```

**Update all shops with full data:**
```
Inputs:
- Max listings: 200
- Specific shops: (leave empty)
```

**Quick update for top listings:**
```
Inputs:
- Max listings: 10
- Specific shops: (leave empty)
```

### Security Notes

- The action uses `github-actions[bot]` for commits
- No secrets or API keys required (public Etsy scraping)
- Database is committed to your repository (consider privacy)
- Logs may contain shop names and sales data

### Support

If the action fails:

1. **Check workflow logs** in the Actions tab
2. **Review artifacts** for detailed scraping logs
3. **Test locally** with `python test_scraper.py ShopName`
4. **Check Etsy availability** - ensure website is accessible
5. **Verify shop names** - ensure they're spelled correctly

---

**Quick Links:**
- [Actions Tab](../../actions)
- [Workflow File](../workflows/rescrape-shops.yml)
- [Re-scrape Script](../../rescrape_shops.py)
- [Troubleshooting Guide](../../TROUBLESHOOTING.md)
