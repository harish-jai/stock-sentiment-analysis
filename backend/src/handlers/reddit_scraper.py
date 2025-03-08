import praw
import json
import os
from datetime import datetime

# Load Reddit API credentials from Lambda environment variables
client_id = os.environ['REDDIT_CLIENT_ID']
client_secret = os.environ['REDDIT_CLIENT_SECRET']
user_agent = os.environ['REDDIT_USER_AGENT']

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

def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        subreddit_name = body.get('subreddit')
        query = body.get('query')
        limit = body.get('limit', 100)

        if not subreddit_name or not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'subreddit and query are required parameters'})
            }

        new_posts = get_posts(subreddit_name, query, limit)

        print(f"Fetched {len(new_posts)} posts from r/{subreddit_name}")

        return {
            'statusCode': 200,
            'body': json.dumps(new_posts)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }