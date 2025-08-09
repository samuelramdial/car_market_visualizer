import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re

# Map common make variants to standardized uppercase makes
MAKE_CORRECTIONS = {
    "Chevy": "CHEVROLET",
    "Chevrolet": "CHEVROLET",
    "VW": "VOLKSWAGEN",
    "Volkswagen": "VOLKSWAGEN",
    "Ram": "RAM",
    "F150": "FORD",
    "Ford": "FORD",
    "Acura": "ACURA",
    "BMW": "BMW",
    "Bmw": "BMW",
    "Honda": "HONDA",
    "Hyundai": "HYUNDAI",
    "Toyota": "TOYOTA",
    "Nissan": "NISSAN",
    "Subaru": "SUBARU",
    "Infiniti": "INFINITI",
    "Mercedes-Benz": "MERCEDES-BENZ",
    "Jaguar": "JAGUAR",
    "Dodge": "DODGE",
    "GMC": "GMC",
    # Add more as you find them
}

def normalize_make(make):
    if not make:
        return "UNKNOWN"
    make = make.strip().title()
    # Fix known variants
    standardized = MAKE_CORRECTIONS.get(make, make).upper()
    # Filter out makes that are clearly invalid (like years or weird words)
    if re.match(r'^\d{4}$', standardized):  # If it's a year
        return "UNKNOWN"
    if len(standardized) <= 1:  # Too short to be a make
        return "UNKNOWN"
    return standardized

def clean_name(raw_name):
    if not raw_name:
        return None
    name = raw_name.strip()
    # List of unwanted phrases to remove (case insensitive)
    unwanted_phrases = [
        'automatic', 'clean title', 'miles', 'mpg', 'odometer', 
        'low miles', 'like new', 'estate sale', 'project truck', 
        'runs excellent', '4 cyl', '4 cylinder', '6 cyl', 'v6', 'v8',
        'awd', 'fwd', 'rwd', 'manual', 'transmission', 'gasoline',
        'fuel', 'new tires', 'recently serviced'
    ]
    for phrase in unwanted_phrases:
        name = re.sub(r'\b' + re.escape(phrase) + r'\b', '', name, flags=re.I)
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)
    # Remove leading/trailing punctuation or spaces
    name = name.strip(" -,:;.")
    # Title case, but keep known acronyms uppercase
    name = name.title()
    # Fix some known acronyms to uppercase
    name = re.sub(r'\bAwd\b', 'AWD', name)
    name = re.sub(r'\bV\d\b', lambda m: m.group().upper(), name)
    name = re.sub(r'\b4 Cyl\b', '4 Cyl', name)
    return name.strip()

def extract_make_from_name(name):
    if not name:
        return None
    # Make assumption: first word after year (if year present) or first word overall is make
    # Remove leading year if present
    parts = name.split()
    if len(parts) == 0:
        return None
    if re.match(r'^\d{4}$', parts[0]):
        # Year present, so make might be second word
        if len(parts) > 1:
            return parts[1]
        else:
            return None
    else:
        return parts[0]

def convert_price_to_float(price_str):
    if not price_str:
        return None
    price_str = str(price_str).strip()
    # Remove $ or commas
    price_str = price_str.replace('$', '').replace(',', '')
    try:
        return float(price_str)
    except ValueError:
        return None

def scrape_craigslist():
    url = "https://raleigh.craigslist.org/search/cta?purveyor=owner"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # Find the JSON script tag containing listings
    script_tag = soup.find('script', {'type': 'application/ld+json', 'id': 'ld_searchpage_results'})
    if not script_tag:
        print("Could not find JSON script tag.")
        return pd.DataFrame()

    data = json.loads(script_tag.string)
    listings = data.get("itemListElement", [])

    cars = []
    for listing in listings:
        item = listing.get("item", {})

        raw_name = item.get("name")
        cleaned_name = clean_name(raw_name)
        raw_make = extract_make_from_name(cleaned_name)
        normalized_make = normalize_make(raw_make)

        raw_price = item.get("offers", {}).get("price")
        price = convert_price_to_float(raw_price)

        location = item.get("offers", {}).get("availableAtOrFrom", {}).get("address", {}).get("addressLocality")

        latitude = item.get("offers", {}).get("availableAtOrFrom", {}).get("geo", {}).get("latitude")
        longitude = item.get("offers", {}).get("availableAtOrFrom", {}).get("geo", {}).get("longitude")

        car = {
            "name": cleaned_name,
            "price": price,
            "location": location,
            "make": normalized_make,
            "latitude": latitude,
            "longitude": longitude
        }
        cars.append(car)

    df = pd.DataFrame(cars)
    return df

if __name__ == "__main__":
    df = scrape_craigslist()
    print(df.head())
    # Optionally save to CSV for Tableau later
    df.to_csv("craigslist_cars_cleaned.csv", index=False)
