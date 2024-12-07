Market Firehose: 
Build a system that can handle 100 articles per minute. Your system should be able to process unstructured text articles and parse out the publisher, author, date, title, body, related sector. This should include an API and database schema. It must be a highly extensible system that can support articles from many different feeds, allows others to subscribe to the system to receive structured articles, and must operate as close to real time as possible while being able to handle processing hundreds of articles per minute.

This project is trying to build a handler to get many articles as quick as possible and analyze them to see which would be a good choice to use for market analysis.

To start the scraping of all the news sources:
I recommend using a virtual environment
`pip3 install -r requirements.txt`
`python3 main.py`

In order to view all the markdown articles:
`python3 read_news_content.py`

This project uses Olostep https://www.olostep.com/
