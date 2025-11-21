import logging
import os
from scraper.firecrawl_client import FirecrawlClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firecrawl():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY not set")
        return

    client = FirecrawlClient(api_key=api_key)
    url = "https://www.etsy.com/shop/PlannerKate1"
    
    logger.info(f"Testing Firecrawl with URL: {url}")
    response = client.get(url)
    
    if response:
        logger.info("Success! Got response.")
        logger.info(f"Response length: {len(response.text)}")
        if "PlannerKate1" in response.text:
            logger.info("Found shop name in response.")
        else:
            logger.warning("Shop name not found in response.")
    else:
        logger.error("Failed to get response.")

if __name__ == "__main__":
    test_firecrawl()
