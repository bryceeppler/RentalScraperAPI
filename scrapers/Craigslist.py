from typing import List
from playwright.async_api import async_playwright
import sys
import httpx
from bs4 import BeautifulSoup

async def scrape_craigslist(min_price: int, max_price: int) -> List[dict]:
    url = f"https://victoria.craigslist.org/search/victoria-bc/apa?hasPic=1&lat=48.4272&lon=-123.359&max_price={max_price}&minSqft=800&min_bedrooms=2&min_price={min_price}&search_distance=3.3#search=1~gallery~0~0"
    
    listings = []
    post_links = []

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url)

            await page.wait_for_selector('div.gallery-card')

            posts = await page.query_selector_all('div.gallery-card')
            print(f"found {len(posts)} posts")

            for post in posts:
                try:
                    link_element = await post.query_selector('a.titlestring')
                    link = await link_element.get_attribute('href')

                    post_links.append(link)
                except Exception as e:
                    print(e)
                    print(f' Error on line {sys.exc_info()[-1].tb_lineno}')

            await browser.close()

        except Exception as e:
            print(e)
            print(f' Error on line {sys.exc_info()[-1].tb_lineno}')

    for link in post_links:
        async with httpx.AsyncClient() as client:
            response = await client.get(link)
        
        soup = BeautifulSoup(response.text, 'lxml')

        title = soup.select_one('#titletextonly').text
        price = soup.select_one('.price').text
        location = soup.select_one('div.mapaddress').text.strip() if soup.select_one('div.mapaddress') else "N/A"
        posted_at = soup.select_one('.date.timeago')['datetime']
        thumbs = soup.select_one('div#thumbs')
        images = [link['href'] for link in thumbs.select('a') if link['href']]

        description = soup.select_one('#postingbody').text.replace('\n\nQR Code Link to This Post\n\n\n','').strip()

        listings.append({
            "title": title,
            "price": float(price.replace('$', '').replace(',', '')),
            "location": location,
            "link": link,
            "images": images,
            "description": description,
            "posted_at": posted_at
        })

    return listings
