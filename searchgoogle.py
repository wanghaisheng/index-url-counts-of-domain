import requests
from bs4 import BeautifulSoup
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient

class MongoDBHandler:
    def __init__(self, connection_string, db_name, collection_name):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_url(self, url, timestamp):
        document = {
            "url": url,
            "timestamp": timestamp
        }
        self.collection.insert_one(document)

def get_date_pairs(year_month):
    start_date = datetime.strptime(year_month + '-01', '%Y-%m-%d')
    end_date = (start_date + timedelta(days=31)).replace(day=1)
    current_date = start_date

    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        yield (current_date.strftime('%Y-%m-%d'), next_date.strftime('%Y-%m-%d'))
        current_date = next_date

def fetch_urls(start_date, end_date, count, tag_prefix):
    url_template = "https://www.google.com/search?q=site:{}+after:{}+before:{}&start={}"
    url = url_template.format(tag_prefix, start_date, end_date, count)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if 'tiktok.com/tag/' in href:
            links.append(href)

    return links

def main(month, tag_prefix, mongodb_uri):
    print(f"Searching for URLs in month: {month} with tag prefix: {tag_prefix}")
    count = 0
    max_count = 1000
    urls_found = set()

    for start_date, end_date in get_date_pairs(month):
        while count < max_count:
            urls = fetch_urls(start_date, end_date, count, tag_prefix)
            if not urls:
                break
            urls_found.update(urls)
            count += 10

    # MongoDB configuration
    db_name = "emartdb"
    collection_name = "urls"
    db_handler = MongoDBHandler(mongodb_uri, db_name, collection_name)

    # Save URLs to MongoDB
    timestamp = datetime.utcnow()
    for url in urls_found:
        db_handler.insert_url(url, timestamp)

    print(f"Found {len(urls_found)} unique URLs and saved them to MongoDB.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python search.py YYYY-MM tag_prefix mongodb_uri")
        sys.exit(1)
    
    month = sys.argv[1]
    tag_prefix = sys.argv[2]
    mongodb_uri = sys.argv[3]
    main(month, tag_prefix, mongodb_uri)
