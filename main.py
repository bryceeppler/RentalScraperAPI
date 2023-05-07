from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from pydantic import BaseModel
from scrapers.Craigslist import scrape_craigslist
from scrapers.Kijiji import scrape_kijiji
import redis
import os
import asyncio
import dotenv
import sys
import json
dotenv.load_dotenv()
from scrapers.UsedVictoria import scrape_used_victoria

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


async def scrape_listings(min_price: int, max_price: int):
    try:
        print("Background scraping task started...")
        
        tasks = [
            scrape_craigslist(min_price, max_price),
            scrape_kijiji(min_price, max_price),
            scrape_used_victoria(min_price, max_price),
        ]
        
        results = await asyncio.gather(*tasks)
        
        craigslist_listings, kijiji_listings, used_victoria_listings = results

        print("Scraping task completed...")

        print(f"Found {len(craigslist_listings)} craigslist listings")
        print(f"Found {len(kijiji_listings)} kijiji listings")
        print(f"Found {len(used_victoria_listings)} used victoria listings")

        

        all_listings = craigslist_listings + kijiji_listings + used_victoria_listings
        
        all_listings.sort(key=lambda x: x['posted_at'], reverse=True)

        rd.set('listings', json.dumps(all_listings))
        rd.expire('listings', 60 * 60 * 24)
        print("Cache updated...")
        return all_listings
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


@app.get("/fetchNoBackgroundTasks")
async def fetchNoBackgroundTasks():
    # same as fetch but without background tasks, return the results
    return await scrape_listings(1500, 3000)


@app.get("/craigslist")
async def craigslist():
    # test the craiglist scraper and return the results
    return await scrape_craigslist(1000, 1400)

@app.get("/kijiji")
async def kijiji():
    # test the kijiji scraper and return the results
    return await scrape_kijiji(1000, 1100)

@app.get("/usedvictoria")
async def usedvictoria():
    # test the usedvictoria scraper and return the results
    return await scrape_used_victoria(1500, 3000)

###########################################################################################

from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
from typing import List

def filter_addresses_within_polygon(addresses: List[str], polygon: Polygon) -> List[str]:
    print("Filtering addresses...")
    geolocator = Nominatim(user_agent="myGeocoder", timeout=10)
    filtered_addresses = []
    for address in addresses:
        print(f"check address {address}")        
        location = geolocator.geocode(address)
        if location:
            print(f"location found for {address}")
            point = Point(location.longitude, location.latitude)
            print(f"Longitude: {location.longitude} Latitude: {location.latitude}")
            if polygon.contains(point):
                filtered_addresses.append(address)

    return filtered_addresses

@app.get("/region")
async def region():
    # retrieve data from redis
    if not rd.ping():
        return {"error": "Cache not connected!"}
    if rd.exists('listings'):
        listings = json.loads(rd.get('listings'))
    else:
        return {"error": "Cache miss!"}

    # Define your polygon as a list of (longitude, latitude) coordinates
    polygon_coordinates = [
(-123.416875, 48.454496),
(-123.377981, 48.452034),
(-123.356446, 48.439739),
(-123.355501, 48.417981),  
(-123.317303, 48.420317),
(-123.321145, 48.478886),
(-123.236606, 48.484395),
(-123.235079, 48.387400),
(-123.418772, 48.393485),
    ]



    polygon = Polygon(polygon_coordinates)

    addresses = []
    for listing in listings:
        if listing['location']:
            addresses.append(listing['location'])
            print(listing['location'])

    # addresses = [
    #     "1463 Westall Ave, Victoria", # OUTSIDE POLYGON
    #     "1001 Terrace Ave, Victoria", # OUTSIDE POLYGON
    #     "628 Transit Rd, Victoria", # INSIDE POLYGON
    #     "395 Tyee Rd, Victoria", # INSIDE POLYGON
    #     "2464 Central Ave, Victoria", # INSIDE
    #     '218 Wildwood Ave, Victoria', # INSIDE
    #     '610 Dunedin St, Victoria', # INSIDE ON GORGE
    #     '1266 Newport Ave, Victoria', # INSIDE
    # ]

    filtered_addresses = filter_addresses_within_polygon(addresses, polygon)
    print(filtered_addresses)
    return filtered_addresses
