import pandas as pd
import csv
from sklearn import linear_model
from sklearn.model_selection import train_test_split
from preprocessing import *
import flair
from flair.data import Sentence
import yfinance as yf
import datetime
import numpy as np

def sentiment_analysis(tweetsList, sentimentFile):
    '''Read the Tweets File, performs sentiment analysis, and writes final dataframe with scores to a csv file'''
   
    # Read list of tweets for the given file and save it to company_tweets
    with open(tweetsList, 'r') as f:
        company_tweets = [int(i) for i in list(csv.reader(f, delimiter=","))[0]]
    
    # For testing purposes only use the first 10,000 tweets
    company_tweets = company_tweets[:100000]
    
    
    def dateparse (time_in_secs):    
        return datetime.datetime.fromtimestamp(float(time_in_secs)).strftime('%Y-%m-%d')

    tweetsFile = "./datasets/Tweet.csv"
   
   # Read the Tweets.csv file and save the tweets related to given ticket in DataFrame
   
    df1 = pd.read_csv(tweetsFile, parse_dates=['post_date'], date_parser=dateparse)
    print(df1.head())
    df = pd.DataFrame(columns=df1.columns)  
    c = 0
    for tweet_id in company_tweets:
        df.loc[tweet_id] = df1.loc[df1['tweet_id'] == tweet_id].values[0]
        print(c)
        c+=1
    print(df.head(10))             
    print("Reading done")
    
    '''
    TODO: Clean up text
    '''
    # df = makeLowercase(df)
    # df["body"] = removeStopwords(df["body"])
    
    '''
    Perform sentiment analysis and save the score
    '''
    sentiment_model = flair.models.TextClassifier.load('en-sentiment')
    # confidence= []
    # sentiment= []
    score = []
    for i, sentence in enumerate(df["body"]):
        sentence = Sentence(sentence)
        sentiment_model.predict(sentence)
        # confidence.append(sentence.labels[0].score)
        # sentiment.append(sentence.labels[0].value)
        if sentence.labels[0].value == "POSITIVE":
            score.append(sentence.labels[0].score)
        else:
            score.append(-sentence.labels[0].score)
        print(i)
    # df["confidence"] = confidence
    # df["sentiment"] = sentiment
    df['score'] = score
    print("sentiment analysis done")

    '''Save to file so you don't have to run this function everytime'''
    df.to_csv(sentimentFile)

def main():
    ticker = "TSLA"
    companytweetsFile = "./datasets/Company_Tweet.csv"
    tweetsListFile = "./datasets/{}_tweets.csv".format(ticker)
    sentimentFile = "stock_sentiment.csv"
    
    '''Sentiment Analysis'''
    # createTweetList(companytweetsFile, tweetsListFile, ticker)
    # sentiment_analysis(tweetsListFile, sentimentFile)

    """Read stock_sentiment.csv and average the score for a given day"""
    df = pd.read_csv(sentimentFile)
    
    df = df[["post_date", "score"]]
    df = df.groupby([df['post_date']]).mean().reset_index()
    print(df.head())

    """"Collect Stock data for the given dates"""
    stock = yf.Ticker(ticker)
    data = stock.history(
        start=df['post_date'].iloc[0],
        end=df['post_date'].iloc[-1],
        interval='1D'
    ).reset_index()
    
    data["Date"] = [str(dt.date()) for dt in data["Date"]]

    """Add the score column from sentiment analysis DataFrame to its corresponding collumn on the stock DataFrame"""
    data["score"] = np.nan
    data["price_change_perc"] = np.nan
    for i,row in data.iterrows():
        data.at[i, "price_change_perc"] = (row['Close'] - row['Open']) / row['Open']
        date = row["Date"]
        if not df[df['post_date'] == date].empty:
            data.at[i, "score"] = df.loc[df['post_date'] == date,"score"]

    print(data.head())


    '''
        TODO: Figure out how we can use the "data" to use sentiment to predict stock movement
    '''
    x = data[['Open','High', 'Low', 'score']]
    y = data['price_change_perc']

    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
    
    # with sklearn
    regr = linear_model.LinearRegression()
    regr.fit(X_train, y_train)

    print('Intercept: \n', regr.intercept_)
    print('Coefficients: \n', regr.coef_)
    print(regr.score(X_test, y_test))

if __name__ == '__main__':
    main()
