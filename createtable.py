import re
import requests
import sqlite3
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
from datetime import datetime
import time

class TwitterClient(object):
    '''
    Generic Twitter Class for sentiment analysis.
    '''
    def __init__(self):
        '''
        Class constructor or initialization method.
        '''
        # keys and tokens from the Twitter Dev Console
        consumer_key = '2qxJNYKgqi5oZcGyKHufpyepZ'
        consumer_secret = 'N3ajyXciuQGLaK5xjSVD370NqEVIlb4nvwsdJpynOJkgjOh6Z0'
        access_token = '962822930081239040-SbuVkXxUcvIIuCT6GU5pL1hrJ1exBlV'
        access_token_secret = 'qljfPt4BlmN6qgqAS7wEgwuXO0nLX4s454Icd71VPI7EP'

        # attempt authentication
        try:
            # create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            # set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            # create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed")

    def clean_tweet(self, tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def get_tweet_sentiment(self, tweet):
        '''
        Utility function to classify sentiment of passed tweet
        using textblob's sentiment method
        '''
        # create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        # set sentiment
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'

    def get_tweets(self, query, count = 10):
        '''
        Main function to fetch tweets and parse them.
        '''
        # empty list to store parsed tweets
        tweets = []

        try:
            # call twitter api to fetch tweets
            fetched_tweets = self.api.search(q = query, count = count)

            # parsing tweets one by one
            for tweet in fetched_tweets:
                # empty dictionary to store required params of a tweet
                parsed_tweet = {}

                # saving text of tweet
                parsed_tweet['text'] = tweet.text
                # saving sentiment of tweet
                parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)

                # appending parsed tweet to tweets list
                if tweet.retweet_count > 0:
                    # if tweet has retweets, ensure that it is appended only once
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                else:
                    tweets.append(parsed_tweet)

            # return parsed tweets
            return tweets

        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))

def main():
    # creating object of TwitterClient Class
    api = TwitterClient()

    conn = sqlite3.connect('DS.db')
    c = conn.cursor()

    #Create the tables first
    c.execute('''Create Table Sentiment(Time BLOB, CC String, Sentiment String, Value float)''')
    c.execute('''CREATE TABLE Price(CC String, PRICE float, MKTCAP float, LASTUPDATE STRING)''')


    while True:
        # calling function to get tweets
        tweetsE = api.get_tweets(query = 'ETH', count = 100)
        tweetsB = api.get_tweets(query = 'BTC', count = 100)
        tweetsL = api.get_tweets(query = 'LTC', count = 100)

        # picking positive tweets from tweets
        ptweetsE = [tweet for tweet in tweetsE if tweet['sentiment'] == 'positive']
        ptweetsB = [tweet for tweet in tweetsB if tweet['sentiment'] == 'positive']
        ptweetsL = [tweet for tweet in tweetsL if tweet['sentiment'] == 'positive']
        # percentage of positive tweets
        #print("Positive tweets percentage: {} %".format(100*len(ptweets)/len(tweets)))
        posE = (float)(len(ptweetsE))/(float)(len(tweetsE))
        posB = (float)(len(ptweetsB))/(float)(len(tweetsB))
        posL = (float)(len(ptweetsL))/(float)(len(tweetsL))

        # picking negative tweets from tweets
        ntweetsE = [tweet for tweet in tweetsE if tweet['sentiment'] == 'negative']
        ntweetsB = [tweet for tweet in tweetsB if tweet['sentiment'] == 'negative']
        ntweetsL = [tweet for tweet in tweetsL if tweet['sentiment'] == 'negative']
        # percentage of negative tweets
        #print("Negative tweets percentage: {} %".format(100*len(ntweets)/len(tweets)))
        negE = (float)(len(ntweetsE))/(float)(len(tweetsE))
        negB = (float)(len(ntweetsB))/(float)(len(tweetsB))
        negL = (float)(len(ntweetsL))/(float)(len(tweetsL))
        # percentage of neutral tweets
        #print("Neutral tweets percentage: {} % \".format(100*(len(tweets) - len(ntweets) - len(ptweets))/len(tweets)))
        neuE = (float)(len(tweetsE) - len(ntweetsE) - len(ptweetsE))/(float)(len(tweetsE))
        neuB = (float)(len(tweetsB) - len(ntweetsB) - len(ptweetsB))/(float)(len(tweetsB))
        neuL = (float)(len(tweetsL) - len(ntweetsL) - len(ptweetsL))/(float)(len(tweetsL))

        st = str(datetime.now()).split('.')[0]
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"BTC","Positive",posB))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"BTC","Negative",negB))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"BTC","Neutral",neuB))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"ETH","Positive",posE))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"ETH","Negative",negE))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"ETH","Neutral",neuE))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"LTC","Positive",posL))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"LTC","Negative",negL))
        c.execute("Insert into Sentiment values (?,?,?,?)", (st,"LTC","Neutral",neuL))
        conn.commit()

        c.execute("Select count(*) from Sentiment")
        conn.commit()
        count = c.fetchall()[0][0]

        if count > 900:
            c.execute("Delete from Sentiment where rowid IN (Select rowid from Sentiment limit 9)")
            conn.commit()

        # printing first 5 positive tweetsnegB
        '''print("\n\nPositive tweets:")
        for tweet in ptweetsE[:10]:
            print(tweet['text'].encode("utf-8"))

        # printing first 5 negative tweets
        print("\n\nNegative tweets:")
        for tweet in ntweetsE[:10]:
            print(tweet['text'].encode("utf-8"))'''

        response = requests.get("https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,LTC&tsyms=USD")

        if response.status_code == 200:
            r=response.json()

        data = []
        data.append("BTC")
        data.append(r['RAW']['BTC']['USD']['PRICE'])
        data.append(r['RAW']['BTC']['USD']['MKTCAP'])
        data.append(datetime.fromtimestamp(r['RAW']['BTC']['USD']['LASTUPDATE']))
        data1 = []
        data1.append("ETH")
        data1.append(r['RAW']['ETH']['USD']['PRICE'])
        data1.append(r['RAW']['ETH']['USD']['MKTCAP'])
        data1.append(datetime.fromtimestamp(r['RAW']['ETH']['USD']['LASTUPDATE']))
        data2 = []
        data2.append("LTC")
        data2.append(r['RAW']['LTC']['USD']['PRICE'])
        data2.append(r['RAW']['LTC']['USD']['MKTCAP'])
        data2.append(datetime.fromtimestamp(r['RAW']['LTC']['USD']['LASTUPDATE']))

        c.execute('INSERT into Price VALUES(?,?,?,?)',(data))
        c.execute('INSERT into Price VALUES(?,?,?,?)',(data1))
        c.execute('INSERT into Price VALUES(?,?,?,?)',(data2))
        conn.commit()

        c.execute("Select count(*) from Price")
        conn.commit()
        count = c.fetchall()[0][0]

        if count > 300:
            c.execute("Delete from Price where rowid IN (Select rowid from Price limit 3)")
            conn.commit()

        time.sleep(10)

    conn.close()

if __name__ == "__main__":
    # calling main function
    main()
