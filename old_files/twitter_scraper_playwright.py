import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def scrape_tweets(username, password, company_name, ticker_symbol, max_tweets=100):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)  # Use headful mode for debugging
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Twitter login page
        await page.goto("https://x.com")
        # Press Sign In button
        await page.click('div.css-146c3p1')
        # Enter username
        await page.fill('input.r-30o5oe', username)
        # Click on next button
        await page.click('button.css-175oi2r')
        # Enter password
        await page.fill('input[name="session[password]"]', password)
        # Click login button
        await page.click('div[data-testid="LoginForm_Login_Button"]')

        # Wait for navigation to complete
        await page.wait_for_navigation()

        # Navigate to Twitter search page
        query = f"{company_name} OR {ticker_symbol}"
        await page.goto(f"https://twitter.com/search?q={query}&src=typed_query")

        # Wait for tweets to load
        await page.wait_for_selector('[data-testid="tweet"]')

        # Extract tweets
        tweets = await page.query_selector_all('[data-testid="tweet"]')
        for tweet in tweets[:max_tweets]:
            html = await tweet.inner_html()
            print(html)

        await browser.close()

if __name__ == "__main__":
    # Retrieve credentials from environment variables
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")

    if not username or not password:
        raise ValueError("Twitter credentials are not set in environment variables.")

    asyncio.run(scrape_tweets(username, password, "Tesla Inc", "TSLA"))