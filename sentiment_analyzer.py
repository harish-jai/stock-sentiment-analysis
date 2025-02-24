import psycopg2
from psycopg2 import sql
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_NAME = 'stock_sentiment'
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = '172.19.32.1'
DB_PORT = '5432'

TICKERS = ['AAPL', 'GOOG', 'GOOGL', 'AMZN', 'TSLA', 'MSFT']
SUBREDDITS = ['stocks', 'wallstreetbets', 'investing', 'daytrading', 'stockmarket']

# Connect to PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

# Perform sentiment analysis on the content
analyzer = SentimentIntensityAnalyzer()
def calculate_sentiment(text):
    score = analyzer.polarity_scores(text)
    return score['compound']

# Analyze sentiment for each ticker
def analyze_sentiment(conn):
    cursor = conn.cursor()
    for ticker in TICKERS:
        print(f"Analyzing sentiment for ticker: {ticker}")
        total_sentiment = 0
        total_posts_all = 0  # Total number of posts across all subreddits
        
        for subreddit in SUBREDDITS:
            print(f"  Processing subreddit: {subreddit}")
            cursor.execute(sql.SQL("""
                SELECT processed_content, score FROM reddit_posts
                WHERE ticker = %s AND subreddit = %s AND processed_content IS NOT NULL
            """), (ticker, subreddit))
            posts = cursor.fetchall()
            subreddit_sentiment = 0
            total_posts = 0  # Number of posts for this subreddit
            
            for content, score in posts:
                sentiment = calculate_sentiment(content)
                weighted_sentiment = sentiment * score
                subreddit_sentiment += weighted_sentiment
                total_posts += 1  # Count each post
            
            if total_posts > 0:  # Calculate subreddit average sentiment
                avg_subreddit_sentiment = subreddit_sentiment / total_posts
                cursor.execute(sql.SQL("""
                    INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        sentiment = EXCLUDED.sentiment, 
                        sample_size = EXCLUDED.sample_size, 
                        calculated_at = EXCLUDED.calculated_at;
                """), (f"{ticker}_{subreddit}", ticker, subreddit, avg_subreddit_sentiment, total_posts, datetime.now()))
                print(f"    Inserted/Updated sentiment for {ticker} in {subreddit}: {avg_subreddit_sentiment} (posts: {total_posts})")
            
            # Accumulate for total sentiment
            total_sentiment += subreddit_sentiment
            total_posts_all += total_posts
            
        if total_posts_all > 0:  # Calculate total average sentiment
            avg_total_sentiment = total_sentiment / total_posts_all
            cursor.execute(sql.SQL("""
                INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    sentiment = EXCLUDED.sentiment, 
                    sample_size = EXCLUDED.sample_size, 
                    calculated_at = EXCLUDED.calculated_at;
            """), (f"{ticker}_all", ticker, "all", avg_total_sentiment, total_posts_all, datetime.now()))
            print(f"  Inserted/Updated total sentiment for {ticker}: {avg_total_sentiment} (posts: {total_posts_all})")
    
    cursor.close()

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        analyze_sentiment(conn)
        conn.close()
        print("Sentiment analysis completed.")
    else:
        print("Failed to connect to the database.")
