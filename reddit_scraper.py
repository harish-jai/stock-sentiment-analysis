import praw
import json
import os
from dotenv import load_dotenv
import argparse

# Load credentials
load_dotenv()
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

def get_posts(subreddit_name, query, limit):
    posts_list = []
    subreddit = reddit.subreddit(subreddit_name)
    for post in subreddit.search(query, sort='new', limit=limit):
        posts_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.selftext,
            'score': post.score,
            'created_utc': post.created_utc,
            'url': post.url,
            'num_comments': post.num_comments
        })
    return posts_list

# Main function to parse arguments and run the scraper
def main():
    parser = argparse.ArgumentParser(description='Reddit Post Scraper for Stock Sentiment Analysis')
    parser.add_argument('--subreddit', type=str, required=True, help='Subreddit to search in (e.g., stocks)')
    parser.add_argument('--stock', type=str, required=True, help='Stock keyword to search for (e.g., Tesla or TSLA)')
    parser.add_argument('--limit', type=int, default=100, help='Number of posts to fetch (default: 100)')

    args = parser.parse_args()
    
    # Get posts
    new_posts = get_posts(args.subreddit, args.stock, args.limit)
    
    # Output results as JSON
    print(json.dumps(new_posts, indent=4))  # Print the posts as JSON

if __name__ == '__main__':
    main()
