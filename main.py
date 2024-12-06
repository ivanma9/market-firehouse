from concurrent.futures import ThreadPoolExecutor
import time
from typing import Tuple
from exceptiongroup import catch
import requests
from bs4 import BeautifulSoup
import os
import http.client, urllib.parse
from dotenv import load_dotenv
import os

from webscraper import WebScraper

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
news_api_key = os.getenv('NEWS_API_KEY')
# from newscatcher import Newscatcher, describe_url


def get_article():
    url = "https://www.theguardian.com/environment/climate-crisis"
    response = requests.get(url)

    print(response.content)

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.find("h1").text
    content = soup.find("article").text
    print("TItle:", title)
    print("Content", content)


def get_news_NewsCatcher():

    # mm = Newscatcher(website = 'mediamatters.org')

    # for index, headline in enumerate(mm.get_headlines()):
    #     print(index, headline)


    nyt = Newscatcher(website = 'theguardian.com')
    results = nyt.get_news()
    count = 0
    
    print(results)
    try:
        articles = results['articles']
        for article in articles[:10]:
            count += 1
            print(
                str(count) + ". " + article["title"] \
                + "\n\t\t" + article["published"] \
                + "\n\t\t" + article["link"]\
                + "\n\n"
                )
            time.sleep(0.33)
    
    except:
        print("cannot find articles")


def get_news():
    num_requests = 10
    num_threads = 4
    print(f"\nMaking {num_requests} concurrent requests...")
    start = time.time()    
        
    # with ThreadPoolExecutor(max_workers=num_threads) as executor:
    #     list(executor.map(lambda _: fetch_slow_api(), range(num_requests)))

    # Run webscraper
    news_urls = ["https://www.theguardian.com/us-news", "https://www.theguardian.com/us", "https://www.bloomberg.com/economics", "https://www.bloomberg.com/markets","https://www.bloomberg.com/industries", "https://www.bloomberg.com/technology", "https://www.bloomberg.com/politics", "https://www.bloomberg.com/businessweek", "https://www.bloomberg.com/opinion", "https://www.bloomberg.com/deals", "https://www.bloomberg.com/markets/fixed-income", "https://www.bloomberg.com/factor-investing", "https://www.bloomberg.com/alternative-investments", "https://www.nytimes.com/section/todayspaper", "https://www.economist.com/", "https://www.newyorker.com/latest", "https://www.latimes.com/", "https://www.chicagotribune.com/", "https://www.chicagotribune.com/business/", "https://www.npr.org/sections/news/", "https://www.washingtonpost.com/", "https://www.washingtonpost.com/business/?itid=hp_top_nav_business", "https://news.google.com/home?hl=en-US&gl=US&ceid=US:en", "https://www.wsj.com/", "https://www.wsj.com/news/latest-headlines?mod=nav_top_section", "https://www.forbes.com/", "https://www.forbes.com/trump/", "https://www.forbes.com/business/", "https://www.reuters.com/", "https://www.bbc.com/news", "https://www.telegraph.co.uk/us/news/", "https://fortune.com/the-latest/", "https://www.businessinsider.com/news", "https://financialpost.com/", "https://time.com/", "https://www.newsweek.com/news"] 
    domain_set = set()
    for url in news_urls:
        base_domain = '.'.join(urllib.parse.urlparse(url).netloc.split('.')[-2:])
        domain_set.add(base_domain)
    scraper = WebScraper(news_urls, domain_set, max_workers=200)
    scraper.start()

    threaded_time = time.time() - start
    print(f"Multi-threaded took: {threaded_time:.2f} seconds")

def fetch_slow_api() -> Tuple[int, str]:
    """Make a request to our slow API and return the status code."""
    try:
        print("Starting request...")
        response = requests.get('http://localhost:5001')
        response.raise_for_status()
        try:
            result = response.json()
            print(f"Request completed: {result}")
            return response.status_code, result['message']
        except ValueError as e:
            print(f"JSON decode error. Response text: {response.text}")
            return -1, f"Invalid JSON response: {str(e)}"
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return -1, str(e)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return -1, str(e)

def get_news_from_page(page_ct):
    # Set the API URL
    url = "https://api.thenewsapi.com/v1/news/all"

    # Prepare the query parameters
    params = {
        'api_token': os.environ.get('NEWS_API_KEY'),
        'categories': 'business,tech',
        # 'search':'',
        'limit': 3,
        'language': 'en',
        'page': page_ct
    }

    # Make the GET request using requests
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response data
        print(response.json())  # Automatically decodes the JSON response
    else:
        print(f"Error: {response.status_code}")
get_news()
