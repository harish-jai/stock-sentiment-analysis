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
        total_sentiment_by_date = {}
        total_posts_by_date = {}

        for subreddit in subreddits:
            cursor.execute(sql.SQL("""
                SELECT id, processed_content, score, created_date FROM reddit_posts
                WHERE ticker = %s AND subreddit = %s AND processed_content IS NOT NULL
            """), (ticker, subreddit))
            posts = cursor.fetchall()
            print(f"Found {len(posts)} posts for {ticker} in r/{subreddit}")

            subreddit_sentiment_by_date = {}
            subreddit_posts_by_date = {}

            for post_id, content, score, created_date in posts:
                sentiment = calculate_sentiment(content)
                created_date_str = created_date.strftime('%Y-%m-%d') if created_date else None
                cursor.execute(sql.SQL("""
                    UPDATE reddit_posts
                    SET sentiment = %s
                    WHERE id = %s
                """), (sentiment, post_id))

                weighted_sentiment = sentiment * score

                if created_date_str not in subreddit_sentiment_by_date:
                    subreddit_sentiment_by_date[created_date_str] = 0
                    subreddit_posts_by_date[created_date_str] = 0

                subreddit_sentiment_by_date[created_date_str] += weighted_sentiment
                subreddit_posts_by_date[created_date_str] += 1

                if created_date_str not in total_sentiment_by_date:
                    total_sentiment_by_date[created_date_str] = 0
                    total_posts_by_date[created_date_str] = 0

                total_sentiment_by_date[created_date_str] += weighted_sentiment
                total_posts_by_date[created_date_str] += 1
            
            print(f"Calculated sentiment for {len(posts)} posts in r/{subreddit}")

            # per subreddit sentiment scores
            for created_date_str, total_sentiment in subreddit_sentiment_by_date.items():
                total_posts = subreddit_posts_by_date[created_date_str]
                avg_sentiment = total_sentiment / total_posts if total_posts > 0 else 0

                print(f"Calculated sentiment for {total_posts} posts on {created_date_str} in r/{subreddit}")
                
                cursor.execute(sql.SQL("""
                    INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at, date, date_str) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, date_str) DO UPDATE SET
                    sentiment = EXCLUDED.sentiment,
                    sample_size = EXCLUDED.sample_size,
                    calculated_at = EXCLUDED.calculated_at
                    RETURNING (xmax = 0) AS inserted
                """), (f"{ticker}_{subreddit}", ticker, subreddit, avg_sentiment, total_posts, datetime.now(), created_date, created_date_str))
                
                result = cursor.fetchone()
                if result and not result[0]:
                    print(f"Conflict triggered for {ticker} on {created_date_str} in r/{subreddit}")
                else:
                    print(f"Inserted new record for {ticker} on {created_date_str} in r/{subreddit}")
        
        # aggregated sentiment across all subreddits
        for created_date_str, total_sentiment in total_sentiment_by_date.items():
            total_posts = total_posts_by_date[created_date_str]
            avg_total_sentiment = total_sentiment / total_posts if total_posts > 0 else 0

            cursor.execute(sql.SQL("""
                INSERT INTO ticker_sentiment (id, ticker, subreddit, sentiment, sample_size, calculated_at, date, date_str) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, date_str) DO UPDATE SET
                sentiment = EXCLUDED.sentiment,
                sample_size = EXCLUDED.sample_size,
                calculated_at = EXCLUDED.calculated_at
            """), (f"{ticker}_all", ticker, "all", avg_total_sentiment, total_posts, datetime.now(), created_date, created_date_str))

        results.append({
            'ticker': ticker,
            'total_sentiment_by_date': total_sentiment_by_date
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
                'body': json.dumps({'results': results}, default=str)
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
