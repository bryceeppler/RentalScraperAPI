from fastapi import FastAPI
from pydantic import BaseModel
from scrapers.Craigslist import scrape_craigslist
# from scrapers.Kijiji import scrape_kijiji
# from scrapers.UsedVictoria import scrape_used_victoria

app = FastAPI()


class fetchInput(BaseModel):
    minPrice: int
    maxPrice: int
    postedAfter: str




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
        craigslist_listings = await scrape_craigslist(inp.minPrice, inp.maxPrice)
        
        # kijiji_listings = await scrape_kijiji(inp.minPrice, inp.maxPrice, inp.postedAfter)
        # used_listings = await scrape_used(inp.minPrice, inp.maxPrice, inp.postedAfter)

        all_listings = craigslist_listings  # + kijiji_listings + used_listings

        return {"listings": all_listings}
    except Exception as e:
        return {"error": str(e)}