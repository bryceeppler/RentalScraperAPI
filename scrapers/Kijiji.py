import httpx
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import List
import random
import asyncio

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

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        
        listings = []

        listing_links = ['https://kijiji.ca' + listing['seoUrl'] for listing in data['pageProps']['listings']]
        # print(f'Found {len(listing_links)} listings on Kijiji.')
        # print(listing_links[:10])
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            for link in listing_links:
                # DELAY
                await asyncio.sleep(random.uniform(1, 2))

                page = await browser.new_page()
                await page.goto(link)
                await page.query_selector('h1:is([class^="title-"])') 

                title_element = await page.query_selector('h1:is([class^="title-"])')
                title = await title_element.text_content() if title_element else "Title not found."

                # Get the price
                price_element = await page.query_selector('div.priceWrapper-1165431705 > span:nth-child(1)')
                if price_element:
                    price = await price_element.text_content()
                    price = int(price.replace(',', '').replace('$', '').strip())
                    # print(f"Price: ${price}")
                else:
                    print("Price not found.")

                                # Get the location
                location_element = await page.query_selector('.address-3617944557')
                if location_element:
                    location = await location_element.text_content()
                    # print(f"Location: {location}")
                else:
                    print("Location not found.")

                # Get the posting time
                time_element = await page.query_selector('.datePosted-383942873 > time')
                if time_element:
                    posting_time = await time_element.get_attribute('datetime')
                    # print(f"Posting Time: {posting_time}")
                else:
                    print("Posting time not found.")



                # Get image links
                image_elements = await page.query_selector_all('.heroImageBackgroundContainer-811153256 picture source')
                image_links = []
                for image_element in image_elements:
                    img_src = await image_element.get_attribute('srcset')
                    if img_src:
                        image_links.append(img_src)
                # print(f"Image Links: {image_links}")


                # Get post description
                description_element = await page.query_selector('.descriptionContainer-231909819')
                if description_element:
                    description = await description_element.inner_html()
                    # print(f"Description: {description}")
                else:
                    print("Description not found.")

                # print("-------------------------------------")

                listing_data = {
                    'title': title,
                    'price': price,
                    'link': link,
                    'location': location,
                    'posted_at': posting_time,
                    'images': image_links,
                    'description': description
                }
                listings.append(listing_data)
                await page.close()

            await browser.close()


        return listings


    else:
        print(f"Error: {response.status_code}")
        return None


