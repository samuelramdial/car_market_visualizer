import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

url = 'https://raleigh.craigslist.org/search/cta'  # Raleigh cars & trucks area

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

script_tag = soup.find('script', {'type': 'application/ld+json', 'id': 'ld_searchpage_results'})

if script_tag:
    data = json.loads(script_tag.string)
    listings = data.get("itemListElement", [])

    cars = []
    for listing in listings:
        item = listing.get("item", {})
        car = {
            "name": item.get("name"),
            "price": item.get("offers", {}).get("price"),
            "location": item.get("offers", {}).get("availableAtOrFrom", {}).get("address", {}).get("addressLocality"),
            "images": item.get("image", []),
        }
        cars.append(car)

    df = pd.DataFrame(cars)
    print(df.head())
else:
    print("Could not find JSON script tag.")
