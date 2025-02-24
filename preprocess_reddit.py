import nltk
import pandas as pd
import psycopg2
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_NAME = 'stock_sentiment'
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = '172.19.32.1'
DB_PORT = '5432'

# Initialize NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Connect to the PostgreSQL database
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

# Convert text to lowercase
def make_lowercase(data):
    data['content'] = data['content'].apply(lambda x: x.lower())
    return data

# Remove stopwords from text
def remove_stopwords(data):
    stop_words = set(stopwords.words('english'))
    data['content'] = data['content'].apply(lambda sentence: " ".join([w for w in word_tokenize(re.sub(r'[^\w\s]', '', sentence)) if w not in stop_words]))
    return data

# Lemmatize words in the text
def lemmatize_words(data):
    lemmatizer = WordNetLemmatizer()
    data['content'] = data['content'].apply(lambda sentence: " ".join([lemmatizer.lemmatize(word) for word in word_tokenize(sentence)]))
    return data

# Clean the content of special characters, URLs, etc.
def clean_text(data):
    data['content'] = data['content'].apply(lambda x: re.sub(r'http\S+|www\S+|https\S+', '', x))  # Remove URLs
    data['content'] = data['content'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x))  # Remove non-alphabetical characters
    return data

# Fetch posts from the database
def fetch_posts_from_db(conn, ticker):
    query = f"""
        SELECT post_id, content
        FROM reddit_posts
        WHERE ticker = '{ticker}' AND processed_content IS NULL
    """
    df = pd.read_sql_query(query, conn)
    return df

# Update the processed content in the database
def update_processed_content(conn, post_id, processed_content):
    try:
        cursor = conn.cursor()
        update_query = """
            UPDATE reddit_posts
            SET processed_content = %s
            WHERE post_id = %s
        """
        cursor.execute(update_query, (processed_content, post_id))
        conn.commit()
        cursor.close()
    except Exception as e:
        print("Error updating processed content:", e)

# Main function to preprocess data
def preprocess_data(ticker):
    conn = connect_db()
    if not conn:
        return

    # Fetch posts for the given ticker
    posts_df = fetch_posts_from_db(conn, ticker)

    # Preprocess the data
    posts_df = make_lowercase(posts_df)
    posts_df = remove_stopwords(posts_df)
    posts_df = lemmatize_words(posts_df)
    posts_df = clean_text(posts_df)

    # Update the processed content in the database
    for index, row in posts_df.iterrows():
        update_processed_content(conn, row['post_id'], row['content'])

    print(f"Preprocessing completed for {ticker} and updated in the database.")
    conn.close()

if __name__ == "__main__":
    TICKERS = ['AAPL', 'GOOG', 'GOOGL', 'AMZN', 'TSLA', 'MSFT']
    for ticker in TICKERS:
        print(f"Preprocessing data for {ticker}...")
        preprocess_data(ticker)
    print("Preprocessing completed for all tickers.")
