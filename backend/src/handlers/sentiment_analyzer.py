import psycopg2
from psycopg2 import sql
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import os

# Environment Variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Sentiment Analyzer
analyzer = SentimentIntensityAnalyzer()

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

def calculate_sentiment(text):
    score = analyzer.polarity_scores(text)
    return score['compound']

def analyze_sentiment(conn, tickers, subreddits):
    cursor = conn.cursor()
    results = []

    for ticker in tickers:
        total_sentiment = 0
        total_posts_all = 0
        
        for subreddit in subreddits:
            cursor.execute(sql.SQL("""
                SELECT id, processed_content, score FROM reddit_posts
                WHERE ticker = %s AND subreddit = %s AND processed_content IS NOT NULL
            """), (ticker, subreddit))
            posts = cursor.fetchall()
            print(f"Found {len(posts)} posts for {ticker} in r/{subreddit}")
            subreddit_sentiment = 0
            total_posts = 0

            for id, content, score in posts:
                sentiment = calculate_sentiment(content)
                cursor.execute(sql.SQL("""
                    UPDATE reddit_posts
                    SET sentiment = %s
                    WHERE id = %s
                """), (sentiment, id))
                print(f"Updated sentiment for post {id} to {sentiment}")
                weighted_sentiment = sentiment * score
                subreddit_sentiment += weighted_sentiment
                total_posts += 1
            
            if total_posts > 0:  # Calculate subreddit average sentiment
                avg_subreddit_sentiment = subreddit_sentiment / total_posts
                cursor.execute(sql.SQL("""
                    INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """), (f"{ticker}_{subreddit}", ticker, subreddit, avg_subreddit_sentiment, total_posts, datetime.now()))
                
            total_sentiment += subreddit_sentiment
            total_posts_all += total_posts
        
        if total_posts_all > 0:  # Calculate total average sentiment
            avg_total_sentiment = total_sentiment / total_posts_all
            cursor.execute(sql.SQL("""
                INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """), (f"{ticker}_all", ticker, "all", avg_total_sentiment, total_posts_all, datetime.now()))
        
        results.append({
            'ticker': ticker,
            'total_sentiment': avg_total_sentiment,
            'total_posts': total_posts_all
        })
    
    cursor.close()
    print("Sentiment analysis completed, generated results for", len(results), "tickers")
    return results

# Lambda Handler
def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        tickers = body.get('tickers', [])
        subreddits = body.get('subreddits', [])

        conn = connect_db()
        if conn:
            results = analyze_sentiment(conn, tickers, subreddits)
            conn.close()
            return {
                'statusCode': 200,
                'body': json.dumps({'results': results})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to connect to the database'})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

