from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
from nltk.stem import WordNetLemmatizer 
import nltk
import re
import csv

def makeLowercase(data):
    data["body"] = data['body'].apply(lambda x: x.lower())
    return data

def removeStopwords(column):
    nltk.download('punkt')
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english')) 
    column = column.apply(lambda sentence: " ".join([w for w in word_tokenize(re.sub(r'[^\w\s]','', sentence)) if not w in stop_words]))
    return column

def lemmatization(column):
    lemmatizer = WordNetLemmatizer()
    column = column.apply(lambda words: [lemmatizer.lemmatize(w) for w in words])
    return column

def createTweetList(companytweetsFile, tweetList, Ticker):
    '''
    Collects list of ids for all tweets tagged with given Ticker saves it to file tweetsList
    '''
    tweet_ids = []
    with open(companytweetsFile, 'r') as f:
        filereader = csv.reader(f)
        for tweet_id,tick in filereader:
            if(tick == Ticker):
                tweet_ids.append(tweet_id)

    with open(tweetList, 'w') as f:
        f.write(",".join(tweet_ids))