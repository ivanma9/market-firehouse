import time
import requests


def make_request(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def scrape_website(start_url):
    print(f"[scrape_website]: Scraping {start_url}")
    endpoint = "https://agent.olostep.com/olostep-p2p-incomingAPI"
    query_params = {
        "token": "olostep_beta_api_a3RqTyB6Qq8cdPr308Gq5LNc9NjAI7NT7v28",
        "url": start_url,
        "timeout": 65,
        "waitBeforeScraping": 1,
        "removeCSSselectors": 'none',
        "nodeCountry": "US",
        "extractLinks": True,
        "absoluteLinks": True,
    }
    json_response = make_request(endpoint, params=query_params)
    if json_response is None:
        return None, None
    else:
        return (json_response['defaultDatasetId'],
                json_response['markdown_content'])


def start():
    print("[start]: ACTIVATED")

    urls_to_test = [
        # "https://www.indeed.com/l-san-francisco,-ca-jobs.html?vjk=c342e832646744a9",
        # "https://efast2-filings-public.s3.amazonaws.com/prd/2024/04/26/20240426094612NAL0011350995001.pdf",
        # "https://www.instagram.com/mondo_marcio/",
        # "https://www.reuters.com/sports/tennis/svitolina-wears-black-ribbon-ukraine-reaches-wimbledon-quarters-2024-07-08/",
        # "https://www.olostep.com/",
        "https://www.theguardian.com/",
        # "https://www.linkedin.com/in/arslan-ali-00957b249/",
        # "http://www.linkedin.com/in/max-brodeur-urbas-1a4b25172/",
        # "https://www.linkedin.com/jobs/linkedin-jobs-washington-dc?position=1&pageNum=0",
        # "http://orderbamboorestaurant.com/",
        # "http://www.reddit.com/r/aww/comments/1cfkvtq/with_a_major_lack_of_storage_on_our_boat_we_still/",
        # "https://www.reddit.com/r/MacOS/comments/1cf3wnz/got_my_macbook_m3_max_stolen_help_to_find_it/",
        # "https://www.reddit.com/r/MacOS/",
        # "https://techcrunch.com/category/venture/",
        # "https://techcrunch.com/",
        # "https://techcrunch.com/2023/12/21/against-pseudanthropy/",
        # "https://bitcoin.org/bitcoin.pdf",
        # "https://www.mesacounty.us/sites/default/files/2022-12/land-development-code-mesa-county-2020-land-development-code-amended-june-28-2022.pdf",
        # "https://interscope.com/",
    ]

    for url in urls_to_test:
        print(f"\n{'=' * 50}")
        print(f"Processing URL: {url}")

        start_time = time.time()
        datasetId, markdown = scrape_website(url)
        end_time = time.time()

        latency = end_time - start_time


        print('datasetId:', datasetId)
        print('Markdown Content:')
        print(markdown if markdown else "No markdown content")
        print(f"Latency: {latency:.2f} seconds")


    print("\nAll URLs processed.")


if __name__ == "__main__":
    print("Starting scraping function")
    start()