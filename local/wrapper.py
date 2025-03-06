import subprocess
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Database connection details
load_dotenv()
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# List of tickers and subreddits
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

# Store post data in the database
def store_in_db(conn, posts):
    try:
        cursor = conn.cursor()
        cursor.execute("SET search_path TO public;")
        insert_query = sql.SQL("""
            INSERT INTO reddit_posts (post_id, ticker, subreddit, title, content, score, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING;
        """)
        
        for post in posts:
            cursor.execute(insert_query, (
                post['id'],
                post['ticker'],
                post['subreddit'],
                post['title'],
                post['content'],
                post['score'],
                datetime.fromtimestamp(post['created_utc'])
            ))
        
        cursor.close()
    except Exception as e:
        print("Error storing data in the database:", e)

# Main function to fetch and store data
def main():
    conn = connect_db()
    if not conn:
        return
    
    for ticker in TICKERS:
        query = f'"{ticker}"'
        for subreddit in SUBREDDITS:
            print(f"Fetching posts for {ticker} in r/{subreddit}...")
            try:
                result = subprocess.run(
                    ['python3', 'reddit_scraper.py', 
                     '--subreddit', subreddit, 
                     '--stock', query, 
                     '--limit', '100'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Error fetching data: {result.stderr}")
                    continue
                
                # Extract posts from JSON output
                posts = json.loads(result.stdout)
                
                # Add additional metadata
                for post in posts:
                    post['ticker'] = ticker
                    post['subreddit'] = subreddit
                
                # Store in PostgreSQL
                store_in_db(conn, posts)
                
            except Exception as e:
                print(f"Error processing {ticker} in r/{subreddit}: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()
