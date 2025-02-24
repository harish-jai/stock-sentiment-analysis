import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def scrape_tweets(company_name, ticker_symbol, max_tweets=100):
    # Define the search query
    query = f"{company_name} OR {ticker_symbol}"
    
    # List to store tweet data
    tweets_data = []

    print(f"Starting to scrape tweets for {company_name} ({ticker_symbol})...")

    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to Twitter search page
        print(f"Navigating to Twitter search page for query: {query}")
        await page.goto(f"https://twitter.com/search?q={query}&src=typed_query")

        # Scroll and collect tweets
        tweet_count = 0
        while tweet_count < max_tweets:
            # Wait for tweets to load
            print("Waiting for tweets to load...")
            await page.wait_for_selector('article')

            # Extract tweets
            print("Extracting tweets...")
            tweets = await page.query_selector_all('article')
            for tweet in tweets:
                if tweet_count >= max_tweets:
                    break
                try:
                    tweet_id = await tweet.get_attribute('data-tweet-id')
                    writer = await tweet.query_selector('div[dir="ltr"] > span').inner_text()
                    post_date = await tweet.query_selector('time').get_attribute('datetime')
                    body = await tweet.query_selector('div[lang]').inner_text()
                    comment_num = await tweet.query_selector('div[data-testid="reply"]').inner_text()
                    retweet_num = await tweet.query_selector('div[data-testid="retweet"]').inner_text()
                    like_num = await tweet.query_selector('div[data-testid="like"]').inner_text()

                    tweets_data.append([
                        tweet_id,
                        company_name,
                        writer,
                        post_date,
                        body,
                        comment_num,
                        retweet_num,
                        like_num
                    ])
                    tweet_count += 1
                    print(f"Collected tweet {tweet_count}/{max_tweets}")
                except Exception as e:
                    print(f"Error extracting tweet: {e}")

            # Scroll down to load more tweets
            print("Scrolling down to load more tweets...")
            await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)  # Wait for 2 seconds

        print("Closing browser...")
        await browser.close()

    # Create a DataFrame
    tweets_df = pd.DataFrame(tweets_data, columns=[
        "tweet_id", "company", "writer", "post_date", "body", "comment_num", "retweet_num", "like_num"
    ])

    # Save to CSV
    output_file = f"{ticker_symbol}_tweets.csv"
    tweets_df.to_csv(output_file, index=False)
    print(f"Saved {len(tweets_df)} tweets to {output_file}")

if __name__ == "__main__":
    # Example usage
    asyncio.run(scrape_tweets("Tesla Inc", "TSLA")) 