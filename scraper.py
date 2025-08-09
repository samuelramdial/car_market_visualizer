import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

URL = "https://raleigh.craigslist.org/search/cta?purveyor=owner"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

res = requests.get(URL, headers=HEADERS)
res.raise_for_status()  # ensure we get a valid response

soup = BeautifulSoup(res.text, 'html.parser')

script_tag = soup.find('script', {'type': 'application/ld+json', 'id': 'ld_searchpage_results'})

if script_tag:
    data = json.loads(script_tag.string)
    listings = data.get("itemListElement", [])

    cars = []
    for listing in listings:
        item = listing.get("item", {})
        offers = item.get("offers", {})
        address = offers.get("availableAtOrFrom", {}).get("address", {})
        geo = offers.get("availableAtOrFrom", {}).get("geo", {})

        name = item.get("name")
        price = offers.get("price")
        latitude = geo.get("latitude")
        longitude = geo.get("longitude")
        location = address.get("addressLocality")

        car = {
            "name": name,
            "price": float(price) if price else None,
            "location": location,
            "make": name.split()[1] if name and len(name.split()) > 1 else None,
            "latitude": latitude,
            "longitude": longitude,
        }
        cars.append(car)

    df = pd.DataFrame(cars)
    print(df.head())
    df.to_csv("car_listings.csv", index=False)
else:
    print("Could not find JSON script tag.")
