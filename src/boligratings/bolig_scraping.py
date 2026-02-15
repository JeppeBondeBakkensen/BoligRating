"""Scrape Boligportalen
#! Goal:
Scrape boligportalen for 100 apartments with the data below
Columns: title, price, size, address, url, posted_date
"""

import asyncio
import json
import re
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

BASE_URL: str = "https://www.boligportal.dk"
APARTMENTS_PER_PAGE = 18
LINKS_CACHE_FILE = Path("data") / "apartment_links.json"
APARTMENT_DETAILS_FILE = Path("data") / "apartmentdetails.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
CONCURRENCY = 10
SEM = asyncio.Semaphore(CONCURRENCY)
TIMEOUT = aiohttp.ClientTimeout(total=20)


async def _fetch_page(session, url):
    """Fetch pages"""
    for attempt in range(3):
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
                return BeautifulSoup(html, "html.parser")
        except (aiohttp.ClientResponseError, asyncio.TimeoutError):  # noqa: UP041
            if attempt == 2:
                raise
            await asyncio.sleep(1.5 * (attempt + 1))


def _get_max_page_number(soup):
    """Extract max number of pages"""
    page_number_selector = "span.css-176v3d"
    # Get every all text from the frontpage on the class
    page_numbers = [el.get_text(strip=True) for el in soup.select(page_number_selector)]

    # Extracting the max number
    pattern = re.compile(r"^\d+$")
    endpage = max([int(endpage) for endpage in page_numbers if pattern.match(endpage)])
    return endpage


def _extract_apartment_links(soup: BeautifulSoup) -> list[str]:
    """Extract apartment links from a page"""
    apartment_link_selector = "a.AdCardSrp__Link.css-1jlpfr4"
    apartment_links = [
        BASE_URL + str(a["href"]) for a in soup.select(apartment_link_selector) if a.get("href")
    ]
    return apartment_links


async def get_apartment_links(session, city: str = "københavn", num_rooms: str = "2-værelser"):
    """Scrape all apartment links from Boligportal for a given city."""

    # Fetch first page to get the number of total pages
    first_page_url = f"{BASE_URL}/lejligheder/{city}/"
    soup = await _fetch_page(session, first_page_url)
    max_page = _get_max_page_number(soup)

    page_urls = [
        first_page_url if page == 0 else f"{first_page_url}?offset={page * APARTMENTS_PER_PAGE}"
        for page in range(max_page)
    ]
    print(f"🔍 Fetching {max_page} listing pages concurrently...")
    soups = await asyncio.gather(*[_fetch_page(session, url) for url in page_urls])

    apartmentLinks = []
    for page_num, soup in enumerate(soups, start=1):
        # Extract links from the fetched page
        if soup is not None:
            links = _extract_apartment_links(soup)
        else:
            links = []
        apartmentLinks.extend(links)
        print(f"📋 Page {page_num}/{max_page}: Found {len(links)} apartments")

    print(f"✅ Total: {len(apartmentLinks)} apartment links")
    return apartmentLinks


async def get_apartment_links_chased(
    city: str = "københavn", num_rooms: str = "2-værelser", refresh: bool = False
) -> list[str]:
    """If cached the get existing files"""

    cache_file = LINKS_CACHE_FILE

    if cache_file.exists() and not refresh:
        with open(cache_file, encoding="utf-8") as f:
            print(f"📦 Loading {cache_file} from cache...")
            return json.load(f)

    # Scrape fresh data
    print("🔍 Scraping fresh data...")
    async with aiohttp.ClientSession() as session:
        links = await get_apartment_links(session, city, num_rooms)

    # Save to cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved {len(links)} links to {cache_file}")

    return links


async def _scrape_single_apartment(session, page_url):
    async with SEM:
        soup = await _fetch_page(session, page_url)

    if soup is None:
        print(f"⚠️ Failed to fetch or parse page: {page_url}")
        return None

    apartmentDetailsKeys = [el.get_text(strip=True) for el in soup.select("span.css-1td16zm")]
    apartmentDetailsValues = [el.get_text(strip=True) for el in soup.select("span.css-1f8murc")]

    apartment = dict(zip(apartmentDetailsKeys, apartmentDetailsValues))
    apartment["url"] = page_url
    return apartment


async def get_apartment_details(refresh_links: bool = False):
    links = await get_apartment_links_chased(refresh=refresh_links)
    links = list(dict.fromkeys(links))
    # Step 2: Scrape all apartment details concurrently
    print(f"\n📦 Scraping {len(links)} apartment details concurrently...")
    async with aiohttp.ClientSession() as session:
        tasks = [_scrape_single_apartment(session, link) for link in links]
        apartments = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out errors
    apartments = [apt for apt in apartments if isinstance(apt, dict)]
    print(f"✅ Successfully scraped {len(apartments)} apartments")
    return apartments


async def get_apartment_details_cashed(refresh: bool = False):
    cache_file = APARTMENT_DETAILS_FILE

    if cache_file.exists() and not refresh:
        with open(cache_file, encoding="utf-8") as f:
            print(f"📦 Loading {cache_file} from cache...")
            return json.load(f)

    # Scrape fresh data
    print("🔍 Scraping fresh data...")
    apartment_details = await get_apartment_details()

    # Save to cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(apartment_details, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    apartments = asyncio.run(get_apartment_details_cashed(refresh=True))
