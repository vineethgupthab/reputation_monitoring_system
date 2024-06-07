import os
import re
import sys
import pathlib
import requests
import pickle
import random
from datetime import date, timedelta, datetime
import pandas as pd
import urllib.request
from tqdm import tqdm
from gnews import GNews
from urllib.error import HTTPError
from datetime import date, timedelta


def get_full_text(article, world_news_api):
    """
    Retrieve the full text content of an article using the World News API.

    Args:
        article (dict): Dictionary containing information about the article.
        world_news_api (str): API key for accessing the World News API.

    Returns:
        dict: Dictionary containing the full text content of the article.
    """
    url = f"https://api.worldnewsapi.com/extract-news?analyze=true&url=\
        {article['url']}&api-key={world_news_api}"
    url_content = requests.get(url).json()
    return url_content


def get_all_articles_details(articles, old_titles, start_date):
    """
    Retrieve details of all articles, including full
    text content, sentiment, and entities.

    Args:
        articles (list): List of dictionaries
        containing information about each article.
        keyword (str): Keyword for filtering articles.
        count (int): Counter for accessing API keys.
        old_titles (list): List of titles of previously fetched articles.

    Returns:
        list: List of dictionaries containing detailed
        information about each article.
    """
    with open('/Users/vineethguptha/fhlbsf/world_news_api_keys.pickle', 'rb') as handle:
        world_news_api_keys = pickle.load(handle)
    
    valid_articles = []
    
    for news in tqdm(articles):
        if old_titles is not None and news['title'] in old_titles:
            continue
        try:
            article = get_full_text(news, random.choice(world_news_api_keys))
        except:
            continue
        try:
            article_date = datetime.strptime(article['publish_date'], '%Y-%m-%d %H:%M:%S').date()
            if article_date < start_date:
                continue
        except KeyError:
            continue
        print('Article is valid!')
        news['content'] = article['text']
        news['image'] = article['image']
        news['publisher'] = news['publisher']['title']
        match = re.search(r'\d{4}-\d{2}-\d{2}', article['publish_date'])
        news['publish_date'] = match.group()
        news['default_sentiment'] = article['sentiment']
        news['entities'] = article['entities']
        valid_articles.append(news)
        print(len(valid_articles))
    return valid_articles


def get_google_news(topic, old_titles, start_date):
    """
    Retrieve news articles from Google News based on a given topic.

    Args:
        topic (str): Topic for searching news articles.
        count (int): Counter for accessing API keys.
        old_titles (list): List of titles of previously
        fetched articles.
        start_date (tuple): Tuple containing the start date for
        searching news articles.

    Returns:
        list: List of dictionaries containing detailed
        information about each news article.
    """
    google_news = GNews(language='en', country='US',
                        period='7d') # , start_date=start_date add this to get news from a specific date
    results = google_news.get_news(f'"{topic}"')
    print('Googling is done!', len(results))
    data = get_all_articles_details(results, old_titles, start_date)
    return data


if __name__ == '__main__':
    with open('topics.txt', 'r') as f:
        for line in f.readlines():
            topic = line.strip()
            print(topic)
            start_date = date.today() - timedelta(days=2)
            # start_date = (start_date.year, start_date.month, start_date.day)
            filename = f'news/{topic}.csv'
            if os.path.exists(filename):
                old_df = pd.read_csv(filename)
                old_titles = old_df['title'].values
                old_df = pd.read_csv(filename)
                df = pd.DataFrame(get_google_news(topic,
                                                  old_titles,
                                                  start_date), columns=old_df.columns)
                merged_df = pd.concat([old_df, df], ignore_index=True)
                merged_df.to_csv(filename, index=False)
            else:
                #old_df = pd.read_csv('news/First Republic Bank.csv', nrows=5)
                df = pd.DataFrame(
                    get_google_news(topic, [], start_date=start_date),
                    columns=[ 'title', 'description', 'published date', 'url', 'publisher', 'content', 'image', 'publish_date', 'default_sentiment', 'entities', 'is_present'])
            df['is_present'] = df['content'].str.lower().str.contains(topic.lower())
            df = df[df['is_present']==True]
            df.reset_index(inplace=True)
            df.drop(columns='index', inplace=True)
            to_filename = f'intermediate/{topic}.csv'
            df.to_csv(to_filename, index=False)
            df.to_csv(filename, index=False)
