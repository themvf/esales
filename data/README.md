# Sales Data Directory

This directory contains historical Etsy sales tracking data.

## File Structure

### Daily Snapshots
- **Format**: `{shop_name}_YYYYMMDD.json`
- **Example**: `ThePrintedPeanut_20251109.json`
- **Content**: Complete snapshot of shop data for that day
- **Usage**: Easy to review a specific day's data

### Historical Logs
- **Format**: `{shop_name}_history.jsonl`
- **Example**: `ThePrintedPeanut_history.jsonl`
- **Content**: Line-delimited JSON with all historical entries
- **Usage**: Analyze trends over time

## Data Collection

Data is collected daily at 7 AM EST via GitHub Actions.

## File Retention

- Daily snapshots are kept indefinitely for historical analysis
- GitHub Actions also uploads artifacts with 30-day retention as backup

## Privacy Note

This data is scraped from publicly available Etsy shop pages. All information is already publicly accessible on Etsy.com.
