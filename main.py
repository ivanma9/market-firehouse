import time
from exceptiongroup import catch
import requests
from bs4 import BeautifulSoup
import os
import http.client, urllib.parse
from dotenv import load_dotenv
import os

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
    for page_ct in range(50):
        get_news_from_page(page_ct)
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
