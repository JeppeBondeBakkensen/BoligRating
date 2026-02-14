"""Scrape Boligportalen
#! Goal:
Scrape boligportalen for 100 apartments with the data below
Columns: title, price, size, address, url, posted_date
"""

import re

import requests
from bs4 import BeautifulSoup

BASE_URL: str = "https://www.boligportal.dk"
APARTMENTS_PER_PAGE = 18


def get_apartment_links(city: str = "københavn", num_rooms: str = "2-værelser"):
    """Scrape all apartment links from Boligportal for a given city."""

    # Fetch first page to get the number of total pages
    first_page_url = f"{BASE_URL}/lejligheder/{city}/"
    soup = _fetch_page(first_page_url)

    max_page = _get_max_page_number(soup)

    apartmentLinks = []
    for page in range(max_page):
        offset = page * APARTMENTS_PER_PAGE
        page_url = first_page_url if offset == 0 else f"{first_page_url}?offset={offset}"
        print(f"🔍 Page {page + 1}/{max_page}: {page_url}")

        # Fetch the page
        page_soup = _fetch_page(page_url)

        # Extract links from the fetched page
        links = _extract_apartment_links(page_soup)
        apartmentLinks.extend(links)

    return apartmentLinks


def _fetch_page(url) -> BeautifulSoup:
    """Fetch and parse page"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


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
        BASE_URL + str(a["href"])  # Get actual href, not page_url
        for a in soup.select(apartment_link_selector)
        if a.get("href")
    ]
    return apartment_links


if __name__ == "__main__":
    links = get_apartment_links()
    print(links)
    print(len(set(links)))


# apartmentDetailsKeysSelector = "span.css-1td16zm"
# apartmentDetailsValuesSelector = "span.css-1f8murc"
# apartmentDetailsKeys = [el.get_text(strip=True) for el in soup.select(apartmentDetailsKeysSelector)]
# apartmentDetailsValues = [
#     el.get_text(strip=True) for el in soup.select(apartmentDetailsValuesSelector)
# ]

# apartmentDetails = {}
# for key, value in zip(apartmentDetailsKeys, apartmentDetailsValues):
#     apartmentDetails[key] = value

# apartmentList = [apartmentDetails]


# # save to csv
# with open("apartments.csv", "w", newline="", encoding="utf-8") as f:
#     fieldnames = list(apartmentList[0].keys())
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(apartmentList)
