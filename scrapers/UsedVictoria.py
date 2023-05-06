import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List
import sys
import re
from datetime import datetime
from dateutil.parser import parse
from datetime import date, time


def convert_posted_at(date_str):
    if isinstance(date_str, str):
        date_obj = parse(date_str, default=datetime.combine(date.min, time.min))
    elif isinstance(date_str, datetime):
        date_obj = date_str
    elif isinstance(date_str, date):
        date_obj = datetime.combine(date_str, time.min)
    # elif isinstance(date_str, datetime.date):
    #     date_obj = datetime.combine(date_str, time.min)
    else:
        raise TypeError(f"Unsupported input type: {type(date_str)}")

    return date_obj.isoformat()

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def get_listings_from_page(url: str) -> List[str]:
    async with aiohttp.ClientSession() as session:
        response_text = await fetch_url(session, url)

    soup = BeautifulSoup(response_text, 'html.parser')
    listing_elements = soup.find_all("a", class_="ad-list-item-link")
    listing_urls = ["https://www.usedvictoria.com" + elem["href"] for elem in listing_elements]

    return listing_urls

async def scrape_used_victoria(min_price: int, max_price: int) -> List[dict]:
    base_url = f"https://www.usedvictoria.com/real-estate-rentals?r=greatervictoria&ca=%7B%227%22%3A%5B%222%22,null%5D%7D&priceTo={max_price}&priceFrom={min_price}&xflags=wanted"
    listings = []
    post_links = []

    try:

        # Get the first page links
        post_links.extend(await get_listings_from_page(base_url))


        # Get the second page links
        async with aiohttp.ClientSession() as session:
            response_text = await fetch_url(session, base_url)
        soup = BeautifulSoup(response_text, 'html.parser')
        next_page_element = soup.find("a", text="next", class_="border-left")
        if next_page_element:
            next_page_url = "https://www.usedvictoria.com" + next_page_element["href"]
            post_links.extend(await get_listings_from_page(next_page_url))


    except Exception as e:
        print(f'Error on line {sys.exc_info()[-1].tb_lineno}, {type(e).__name__}, {e}')
        print("Error getting links from UsedVictoria.com")

    try:
        # Scrape individual listings
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, link) for link in post_links]
            pages = await asyncio.gather(*tasks)

        for link, page_text in zip(post_links, pages):
            soup = BeautifulSoup(page_text, 'html.parser')

            full_title_element = soup.select_one('div.col.h4.mb-0 > span')
            full_title = full_title_element.text.strip()

                # Use regular expressions to extract price and title
            price_pattern = r"\$(\d+(?:,\d{3})*)"  # Matches prices like $2,800, $1500
            price = float(re.search(price_pattern, full_title).group(1).replace(",", ""))

            title_pattern = r"^\$\d+(?:,\d{3})*\s*[··]\s*(.+)$"  # Matches titles after price and separator
            title = re.search(title_pattern, full_title).group(1)

            # get image container using xpath
            # //*[@id="used-content"]/div/div/div[1]/div[1]/div[1]/div[2]
            # image_container = 
            image_elements = soup.select("div.adview-photos > a > img.rounded")

            images = [img["src"] for img in image_elements]
            location = None

            date_elements = soup.select('div.container.adview-ad-details.rounded.mb-4 > div.row.adview-ad-details-sub.flex-lg-nowrap > div.mr-3.p-3.p-lg-0.col-12.col-lg-7 > div')
            for d in date_elements:
                if 'Posted' in d.text:
                    posted_at = convert_posted_at(d.text.strip().replace('Posted', ''))
                    break
            # get posted at

            # posted_at = soup.select_one("#used-content > div > div > div.row.justify-content-center.justify-content-lg-between > div.two-column-content.col-12.col-lg-auto > div.row.ad-view-container.mb-4 > div.adview-detail-content.p-lg-3 > div.container.adview-ad-details.rounded.mb-4 > div.row.adview-ad-details-sub.flex-lg-nowrap > div.mr-3.p-3.p-lg-0.col-12.col-lg-7 > div:nth-child(3) > div.col-9.bg-white.text-sm.px-2.pt-1 > span").text.strip()
            # convert date to datetime object
            # convert 2021-03-01 to a string 2023-03-22T12:57:12-0700 with default 00:00:00 time like this 2023-03-22T00:00:00-0700
            # posted_at_string = convert_posted_at(posted_at)

            description = soup.select_one('#used-content > div > div > div.row.justify-content-center.justify-content-lg-between > div.two-column-content.col-12.col-lg-auto > div.row.ad-view-container.mb-4 > div.adview-detail-content.p-lg-3 > div.container.adview-ad-details.rounded.mb-4 > div.row.mb-4.p-3.bg-white.rounded.d-block > p').text.strip()

            listings.append({
                "title": title,
                "price": float(price),
                "link": link,
                "location": location,
                "posted_at": posted_at,
                "images": images,
                "description": description
            })
    except Exception as e:
        print(f'Error on line {sys.exc_info()[-1].tb_lineno}, {type(e).__name__}, {e}')
        print("Error scraping individual listings from UsedVictoria.com")

    return listings