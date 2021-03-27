# @author blurpit

import re
import sys

import praw
import tweepy

import secrets

SCOTT_TWITTER_ID = '1120582633'
STATUS_URL = 'https://twitter.com/ScottTheWoz/status/{}'


def get_twitter_auth():
    auth = tweepy.OAuthHandler(
        consumer_key=secrets.TWITTER_API_KEY,
        consumer_secret=secrets.TWITTER_API_SECRET
    )
    auth.set_access_token(
        key=secrets.TWITTER_ACCESS_TOKEN,
        secret=secrets.TWITTER_ACCESS_TOKEN_SECRET
    )
    return auth

def get_reddit_auth():
    reddit = praw.Reddit(
        client_id=secrets.REDDIT_CLIENT_ID,
        client_secret=secrets.REDDIT_CLIENT_SECRET,
        username=secrets.REDDIT_USERNAME,
        password=secrets.REDDIT_PASSWORD,
        user_agent=secrets.REDDIT_USER_AGENT
    )
    reddit.validate_on_submit = True
    return reddit


class TwitterStreamListener(tweepy.StreamListener):
    shorturl_re = re.compile(r'https://t\.co/.{10}')

    def __init__(self, reddit):
        super().__init__()
        self.reddit = reddit

    def on_status(self, status):
        if not status.text.startswith('RT @'): # Ignore retweets
            twitter_url = self.get_tweet_url(status)
            text = self.get_clean_text(status)

            youtube_url = None
            for url in getattr(status, 'extended_entities', status.entities)['urls']:
                url = url['expanded_url']
                if 'youtu.be' in url or 'youtube.com' in url:
                    # Find the first link from youtube.com. Hopefully it's actually
                    # a new scott video cause aint no way I'm checking that lol
                    youtube_url = url
                    break

            print('Text:', text)
            print('URL:', twitter_url)
            print('YT link:', youtube_url)
            # Post tweet to reddit
            post_id = self.reddit.subreddit('test').submit(
                title=text or ('New Scott Video!' if youtube_url else 'New Scott Tweet!'),
                url=youtube_url or twitter_url
            )
            print('Reddit post ID:', post_id)
            print()

    def on_error(self, status_code):
        print(status_code, file=sys.stderr)

    @staticmethod
    def get_tweet_url(status):
        """ Get a link to the tweet """
        return STATUS_URL.format(status.id)

    @classmethod
    def get_clean_text(cls, status):
        """ Remove t.co links from the text of the tweet. """
        if hasattr(status, 'extended_tweet'):
            text = status.extended_tweet['full_text']
        elif hasattr(status, 'full_text'):
            text = status.full_text
        else:
            text = status.text
        return cls.shorturl_re.sub('', text).strip()


def main():
    print('Authenticating twitter...')
    twitter = tweepy.API(get_twitter_auth())
    print('Logged in as:', twitter.me().name)
    print()

    print('Authenticating reddit...')
    reddit = get_reddit_auth()
    print('Logged in as:', reddit.user.me())
    print()

    print('Listening for tweets...')
    print()
    listener = TwitterStreamListener(reddit)
    stream = tweepy.Stream(auth=twitter.auth, listener=listener)
    stream.filter(follow=[SCOTT_TWITTER_ID])

if __name__ == '__main__':
    main()