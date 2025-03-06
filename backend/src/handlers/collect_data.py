import subprocess
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
import boto3

# Load environment variables
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']

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

def store_in_db(conn, posts):
    try:
        cursor = conn.cursor()
        cursor.execute("SET search_path TO public;")
        insert_query = sql.SQL(""" 
            INSERT INTO reddit_posts (post_id, ticker, subreddit, title, content, processed_content, score, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING;
        """)
        
        for post in posts:
            cursor.execute(insert_query, (
                post['id'],
                post['ticker'],
                post['subreddit'],
                post['title'],
                post['content'],
                post['processed_content'],
                post['score'],
                datetime.fromtimestamp(post['created_utc'])
            ))
        
        cursor.close()
    except Exception as e:
        print("Error storing data in the database:", e)

# Text preprocessing functions
def make_lowercase(text):
    return text.lower()

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    return " ".join([w for w in word_tokenize(re.sub(r'[^\w\s]', '', text)) if w not in stop_words])

def lemmatize_words(text):
    lemmatizer = WordNetLemmatizer()
    return " ".join([lemmatizer.lemmatize(word) for word in word_tokenize(text)])

def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)  # Remove URLs
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove non-alphabetical characters
    return text

def preprocess_content(content):
    content = make_lowercase(content)
    content = remove_stopwords(content)
    content = lemmatize_words(content)
    content = clean_text(content)
    return content

def fetch_and_store(tickers, subreddits, preprocess_flag, limit=100):
    conn = connect_db()
    if not conn:
        return
    
    for ticker in tickers:
        query = f'"{ticker}"'
        for subreddit in subreddits:
            print(f"Fetching posts for {ticker} in r/{subreddit}...")
            try:
                client = boto3.client('lambda')
                payload = {
                    "query": query,
                    "subreddit": subreddit,
                    "limit": limit
                }

                result = client.invoke(
                    FunctionName='reddit_scraper_function',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                response_payload = json.loads(result['Payload'].read().decode())
                
                if 'errorMessage' in response_payload:
                    print(f"Error fetching data: {response_payload['errorMessage']}")
                    continue

                posts = json.loads(response_payload['body'])

                print(f"Storing {len(posts)} posts in the database...")
                
                for post in posts:
                    post['ticker'] = ticker
                    post['subreddit'] = subreddit
                    if preprocess_flag:
                        post['processed_content'] = preprocess_content(post['content'])
                    else:
                        post['processed_content'] = None
                
                store_in_db(conn, posts)
                
            except Exception as e:
                print(f"Error processing {ticker} in r/{subreddit}: {e}")
    
    conn.close()

# AWS Lambda handler
def lambda_handler(event, context):
    try:
        # Handle both API Gateway and direct invocation
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])  # API Gateway request
        else:
            body = event  # Direct AWS Lambda test invocation

        tickers = body.get('tickers', [])
        subreddits = body.get('subreddits', [])
        preprocess_flag = body.get('preprocess', True)
        limit = body.get('limit', 100)
        
        if not tickers or not subreddits:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Tickers and subreddits are required"})
            }
        
        fetch_and_store(tickers, subreddits, preprocess_flag, limit)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Lambda function executed successfully",
                "tickers": tickers,
                "subreddits": subreddits,
                "limit": limit
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
