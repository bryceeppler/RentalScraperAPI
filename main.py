from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
async def root():
    return {"message": "Hello World. Welcome to FastAPI!"}


@app.post("/fetch")
async def fetch(inp: fetchInput):
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
    try:
        # print if cache not connected
        if not rd.ping():
            print("Cache not connected!")

        if rd.exists('listings'):
            print("Cache hit!")
            return json.loads(rd.get('listings'))
        print("Cache miss!")
        
        craigslist_listings = await scrape_craigslist(inp.minPrice, inp.maxPrice)
        
        kijiji_listings = await scrape_kijiji(inp.minPrice, inp.maxPrice)
        # used_listings = await scrape_used(inp.minPrice, inp.maxPrice, inp.postedAfter)

        all_listings = craigslist_listings  + kijiji_listings #+ used_listings
        # sort by descending date
        all_listings.sort(key=lambda x: x['posted_at'], reverse=True)
        # convert to json

        rd.set('listings', json.dumps(all_listings))
        rd.expire('listings', 60*60*24)
        # all_listings = kijiji_listings

        return all_listings
    except Exception as e:
        print(f'Error on line {sys.exc_info()[-1].tb_lineno}, {type(e).__name__}, {e}')
        return {"error": str(e)}