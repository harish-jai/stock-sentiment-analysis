import subprocess

# Define the list of tickers and subreddits
tickers = ['AAPL', 'GOOG', 'GOOGL', 'AMZN', 'TSLA', 'MSFT']
subreddits = ['stocks', 'wallstreetbets', 'investing', 'daytrading', 'stockmarket']

# Define the maximum number of posts per query
max_posts = 100  # You can adjust this based on your need

# Define the output CSV filename base
output_filename_base = "reddit_posts"

# Run the scraper for each combination of ticker and subreddit
for ticker in tickers:
    for subreddit in subreddits:
        output_filename = f"/scraped_data/{output_filename_base}_{subreddit}_{ticker}.csv"
        query = f'"{ticker}" OR "{subreddit}"'
        
        # Build the command to run the existing scraper
        command = [
            'python3', 'reddit_scraper.py',
            '--subreddit', subreddit,
            '--stock', query,
            '--limit', str(max_posts),
            '--output', output_filename
        ]
        
        print(f"Running scraper for {ticker} in {subreddit}...")
        subprocess.run(command)

print("Data collection completed for all tickers and subreddits.")
