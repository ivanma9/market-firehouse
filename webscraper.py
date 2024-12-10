import time
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re
from collections import deque
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from threading import Lock
import tiktoken
from embedding import AIModel, extract_text_from_html

encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Returns the number of tokens in the input text."""
    tokens = encoder.encode(text)
    return len(tokens)
class WebScraper:
    def __init__(self, initial_urls, domain_set, max_workers=200):
        self.initial_urls = initial_urls
        self.domain_set = domain_set
        self.processed_urls = set()
        self.all_extracted_urls = set()  # New set to track all URLs found
        self.max_workers = max_workers
        self.csv_lock = Lock()
        self.queue_lock = Lock()
        self.urls_lock = Lock()  # New lock for URL tracking


        # Create/clear the CSV files with headers
        with open('news.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'content'])

        # Create/clear URLs CSV file
        with open('urls.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'is_valid', 'reason_if_invalid'])

    def make_request(self, url, params=None):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None

    def is_valid_url(self, url):
        """Check if URL is valid and matches base domain, excluding sports section"""
        try:
            parsed = urlparse(url)

            # Track invalid reasons
            if not any(parsed.netloc.endswith(valid_domain) for valid_domain in self.domain_set):
                return False, "different_domain"
            if '/sport' in url or '/sports' in url:
                return False, "sports_section"
            if not parsed.scheme in ['http', 'https']:
                return False, "invalid_scheme"
            if not parsed.netloc:
                return False, "no_netloc"

            return True, "valid"
        except:
            return False, "parse_error"

    def log_url(self, url, is_valid, reason):
        """Log URL to CSV file with thread safety"""
        with self.urls_lock:
            if url not in self.all_extracted_urls:
                self.all_extracted_urls.add(url)
                with open('urls.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([url, is_valid, reason])
                # print(f"Found URL: {url} (Valid: {is_valid}, Reason: {reason})")

    def scrape_website(self, url):
        print(f"[scrape_website]: Scraping {url}")
        endpoint = "https://agent.olostep.com/olostep-p2p-incomingAPI"
        query_params = {
            "token": "olostep_beta_api_a3RqTyB6Qq8cdPr308Gq5LNc9NjAI7NT7v28",
            "url": url,
            "timeout": 65,
            "waitBeforeScraping": 0,
            "removeCSSselectors": 'none',
            "nodeCountry": "US",
            "expandHtml": True,
            "extractLinks": True,
            "absoluteLinks": True,
        }
        return self.make_request(endpoint, params=query_params)

    def save_to_csv(self, url, contentId, content):
        """Save results to CSV file with thread safety"""
        with self.csv_lock:
            #Processing content
            print("Saving...", url)
            content = extract_text_from_html(content)
            
            token_count = count_tokens(content)
            print(token_count)
            if (token_count > 6000):
                print("Content too many tokens")
                with open('count.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([token_count, url])    
                return
            ai = AIModel()
            if ai.is_article(content):
                print("ASKING")
                response = ai.ask(content)    
                #Writing to news.csv
                with open('news.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([url, contentId, response])
                return True
            else:
                print("NOT an article, continue crawling")
                return False



    def process_url(self, url):
        """Process a single URL and return new URLs to process"""
        json_response = self.scrape_website(url)
        if not json_response:
            return []

        # Save content to CSV
        content = json_response.get('html_content', '')

        content_id = json_response.get('defaultDatasetId', '')
        found_article = self.save_to_csv(url, content_id, content)

        if (found_article):
            is_valid, reason = self.is_valid_url(url)
            self.log_url(url, is_valid, reason)
            self.processed_urls.add(url)
            return

        # Get new links
        links = json_response.get('links_on_page', [])
        new_links = []

        if links:
            # Process and log all URLs
            for link in links:
                if isinstance(link, str):
                    is_valid, reason = self.is_valid_url(link)
                    self.log_url(link, is_valid, reason)

                    if is_valid:
                        with self.queue_lock:
                            # self.save_to_csv(link, content_id, content)
                            if link not in self.processed_urls:
                                new_links.append(link)
                                self.processed_urls.add(link)

        print(f"Processed {url}, found {len(new_links)} new valid links")
        return new_links

    def start(self):
        print("[start]: ACTIVATED")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {}

            # Start with initial URL
            for initial_url in self.initial_urls:
                future = executor.submit(self.process_url, initial_url)
                future_to_url[future] = initial_url
            while future_to_url:
                # Wait for the next future to complete
                done, _ = as_completed(future_to_url), future_to_url
                for future in done:
                    url = future_to_url[future]
                    try:
                        new_urls = future.result()
                        # Submit new URLs for processing
                        for new_url in new_urls:
                            if new_url not in self.processed_urls and new_url not in self.all_extracted_urls:
                                future_to_url[executor.submit(self.process_url, new_url)] = new_url
                                with self.queue_lock:
                                    self.processed_urls.add(new_url)
                    except Exception as e:
                        print(f"Error processing {url}: {e}")

                    # Remove completed future
                    del future_to_url[future]

                    # Print progress
                    print(f"Processed URLs: {len(self.processed_urls)}")
                    print(f"Total URLs found: {len(self.all_extracted_urls)}")
                    print(f"Queued URLs: {len(future_to_url)}")

        print("\nScraping completed.")
        print(f"Total unique pages processed: {len(self.processed_urls)}")
        print(f"Total unique URLs found: {len(self.all_extracted_urls)}")


def main():
    news_urls = ["https://www.theguardian.com/us-news"]
    # news_urls = ["https://www.theguardian.com/us-news", "https://www.theguardian.com/us", "https://www.bloomberg.com/economics", "https://www.bloomberg.com/markets","https://www.bloomberg.com/industries", "https://www.bloomberg.com/technology", "https://www.bloomberg.com/politics", "https://www.bloomberg.com/businessweek", "https://www.bloomberg.com/opinion", "https://www.bloomberg.com/deals", "https://www.bloomberg.com/markets/fixed-income", "https://www.bloomberg.com/factor-investing", "https://www.bloomberg.com/alternative-investments", "https://www.nytimes.com/section/todayspaper", "https://www.economist.com/", "https://www.newyorker.com/latest", "https://www.latimes.com/", "https://www.chicagotribune.com/", "https://www.chicagotribune.com/business/", "https://www.npr.org/sections/news/", "https://www.washingtonpost.com/", "https://www.washingtonpost.com/business/?itid=hp_top_nav_business", "https://news.google.com/home?hl=en-US&gl=US&ceid=US:en", "https://www.wsj.com/", "https://www.wsj.com/news/latest-headlines?mod=nav_top_section", "https://www.forbes.com/", "https://www.forbes.com/trump/", "https://www.forbes.com/business/", "https://www.reuters.com/", "https://www.bbc.com/news", "https://www.telegraph.co.uk/us/news/", "https://fortune.com/the-latest/", "https://www.businessinsider.com/news", "https://financialpost.com/", "https://time.com/", "https://www.newsweek.com/news"] 
    domain_set = set()
    for url in news_urls:
        base_domain = '.'.join(urlparse(url).netloc.split('.')[-2:])
        domain_set.add(base_domain)
    scraper = WebScraper(news_urls, domain_set, max_workers=200)
    scraper.start()


if __name__ == "__main__":
    print("Starting parallel scraping function")
    main()