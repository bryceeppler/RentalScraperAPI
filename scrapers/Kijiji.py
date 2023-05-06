import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import List
import random
import asyncio
import aiohttp

async def fetch_url(session, url, headers):
    async with session.get(url, headers=headers) as response:
        return await response.text()

async def scrape_kijiji(min_price: int, max_price: int) -> List[dict]:
    url = f'https://www.kijiji.ca/_next/data/NHwrkALSvJDBsWXI0jb4n/en/b-apartments-condos/victoria-bc/3+bedrooms__2+bedrooms__2+bedroom+den__3+bedroom+den__4+bedrooms/c37l1700173a27949001.json?size-sqft=800__&sort=dateDesc&price={min_price}__{max_price}&params=victoria-bc%2F3%2Bbedrooms__2%2Bbedrooms__2%2Bbedroom%2Bden__3%2Bbedroom%2Bden__4%2Bbedrooms%2Fc37l1700173a27949001'

    headers = {
        'authority': 'www.kijiji.ca',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://www.kijiji.ca/b-apartments-condos/victoria-bc/3+bedrooms__2+bedrooms__2+bedroom+den__3+bedroom+den__4+bedrooms/c37l1700173a27949001?size-sqft=800__&sort=dateDesc&price=1337__3600',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'x-nextjs-data': '1',
    }

    async with aiohttp.ClientSession() as session:
        response_text = await fetch_url(session, url, headers)

    data = json.loads(response_text)
    
    listings = []

    listing_links = ['https://kijiji.ca' + listing['seoUrl'] for listing in data['pageProps']['listings']]

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, link, headers) for link in listing_links]
            pages = await asyncio.gather(*tasks)

        for page_text in pages:
            # Add a random delay between requests
            await asyncio.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(page_text, 'lxml')

            # Extract information from the soup object as before
            #
            # Extract the title
            title = soup.find("h1", class_="title-2323565163")
            title = title.get_text(strip=True) if title else "Title not found."

            # Get the price
            price = soup.select_one("div.priceWrapper-1165431705 > span:nth-child(1)")
            price = int(price.get_text(strip=True).replace(",", "").replace("$", "")) if price else None

            # Get the location
            location = soup.select_one(".address-3617944557")
            location = location.get_text(strip=True) if location else "Location not found."

            # Get the posting time
            posted_at = soup.select_one(".datePosted-383942873 > time")
            posted_at = posted_at["datetime"] if posted_at else None

            # Get image links
            image_elements = soup.select(".heroImageBackgroundContainer-811153256 picture source")
            images = [img["srcset"] for img in image_elements if img["srcset"]]

            # Get post description
            description = soup.select_one(".descriptionContainer-231909819")
            description = description.get_text(strip=True) if description else "Description not found."

            # Get the link

            listing_data = {
                "title": title,
                "price": price,
                "link": "",
                "location": location,
                "posted_at": posted_at,
                "images": images,
                "description": description
            }
            listings.append(listing_data)

        await browser.close()

    return listings
