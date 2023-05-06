from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from pydantic import BaseModel
from scrapers.Craigslist import scrape_craigslist
from scrapers.Kijiji import scrape_kijiji
import redis
import os
import dotenv
import sys
import json
dotenv.load_dotenv()
# from scrapers.UsedVictoria import scrape_used_victoria

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class fetchInput(BaseModel):
    minPrice: int
    maxPrice: int
    postedAfter: str


rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)


from typing import Callable

async def scrape_listings(min_price: int, max_price: int):
    try:
        print("Background scraping task started...")
        craigslist_listings = await scrape_craigslist(min_price, max_price)
        kijiji_listings = await scrape_kijiji(min_price, max_price)

        print("Scraping task completed...")

        all_listings = craigslist_listings + kijiji_listings
        all_listings.sort(key=lambda x: x['posted_at'], reverse=True)

        rd.set('listings', json.dumps(all_listings))
        rd.expire('listings', 60 * 60 * 24)
        print("Cache updated...")
    except Exception as e:
        print(f'Error on line {sys.exc_info()[-1].tb_lineno}, {type(e).__name__}, {e}')



@app.get("/")
async def root():
    return {"message": "Hello World. Welcome to FastAPI!"}

@app.get("/all")
async def all():
    if not rd.ping():
        return {"error": "Cache not connected!"}
    if rd.exists('listings'):
        return json.loads(rd.get('listings'))
    return {"error": "Cache miss!"}


@app.post("/fetch")
async def fetch(inp: fetchInput, background_tasks: BackgroundTasks):
    """
    This endpoint will execute the web scrapers for Kijiji, Craigslist and Used.ca

    Returns:
    [{
        "title": "title of the ad",
        "price": "price of the ad",
        "location": "location of the ad",
        "link": "link to the ad"
        "images": "list of images for the ad"
        "description": "description of the ad"
        "postedAt": "date the ad was posted"
    }]
    """
    background_tasks.add_task(scrape_listings, inp.minPrice, inp.maxPrice)
    return {"message": "task started"}

@app.get("/craigslist")
async def craigslist():
    # test the craiglist scraper and return the results
    return await scrape_craigslist(1000, 1400)