import aiohttp
import asyncio
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Read MongoDB URI from environment variables
mongodb_uri = os.getenv('MONGODB_URI')

# Connect to MongoDB
client = MongoClient(mongodb_uri)
db = client['emartdb']
collection = db['domain_index_counts']

# Semaphore to limit concurrency
semaphore = asyncio.Semaphore(10)  # Adjust concurrency limit as needed

async def fetch_indexed_count(session, domain):
    query = f'site:{domain}'
    url = f'https://www.google.com/search?q={query}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    async with semaphore:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            # Parsing result from HTML response
            # This is a placeholder. Actual parsing will depend on the HTML structure.
            # Example: extracting a specific part of the text which indicates indexed count
            start_index = text.find('About') + len('About ')
            end_index = text.find(' results')
            if start_index > -1 and end_index > -1:
                indexed_count = text[start_index:end_index].replace(',', '')
                return int(indexed_count)
            return 'Unable to determine indexed count'

async def save_to_mongodb(domain, index_count):
    document = {
        'domain': domain,
        'index_count': index_count,
        'update_time': datetime.utcnow()
    }

    # Upsert document: update if exists, insert if not
    result = collection.update_one(
        {'domain': domain},
        {'$set': document},
        upsert=True
    )
    return result

async def main(domains):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_indexed_count(session, domain) for domain in domains]
        counts = await asyncio.gather(*tasks)
        for domain, count in zip(domains, counts):
            await save_to_mongodb(domain, count)

if __name__ == '__main__':
    domains = ['example.com', 'example.org', 'example.net']  # List of domains to process
    asyncio.run(main(domains))
