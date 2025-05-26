import requests
import os
import json

BASE_URL = "https://ezanvakti.emushaf.net"

# Determine repository root: one level up from this script's folder.
script_dir = os.path.dirname(os.path.realpath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(repo_root, "data")
os.makedirs(data_dir, exist_ok=True)

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_json(endpoint):
    url = BASE_URL + endpoint
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        validate_json_structure(data, name=endpoint)
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def validate_json_structure(data, name="Data"):
    if isinstance(data, dict):
        print(f"[VALID] {name}: JSON object with keys: {list(data.keys())}")
    elif isinstance(data, list):
        print(f"[VALID] {name}: JSON array with {len(data)} items")
        if data and isinstance(data[0], dict):
            print(f"  Example item keys: {list(data[0].keys())}")
    else:
        print(f"[INVALID] {name}: Unexpected JSON type {type(data)}")

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved data to {filename}")

def fetch_and_save(endpoint, filename):
    if os.path.exists(filename):
        print(f"Skipping {filename} (already exists)")
        return load_json(filename)
    data = fetch_json(endpoint)
    if data:
        save_json(filename, data)
    return data

def main():
    # 1. Fetch Countries
    countries = fetch_and_save("/ulkeler", os.path.join(data_dir, "countries.json"))
    if not countries:
        print("No countries data.")
        return
    
    for country in countries:
        country_id = country.get("UlkeID")
        if not country_id:
            continue
        print(f"Processing country {country.get('UlkeAdiEn', country.get('UlkeAdi'))} with ID: {country_id}")
        
        # 2. Fetch Cities for the Country
        cities = fetch_and_save(f"/sehirler/{country_id}", os.path.join(data_dir, f"cities_{country_id}.json"))
        if not cities:
            continue
        
        for city in cities:
            city_id = city.get("SehirID")
            if not city_id:
                continue
            print(f"  Processing city {city.get('SehirAdiEn', city.get('SehirAdi'))} with ID: {city_id}")
            
            # 3. Fetch Districts for the City
            districts = fetch_and_save(f"/ilceler/{city_id}", os.path.join(data_dir, f"districts_{city_id}.json"))
            if not districts:
                continue
            
            for district in districts:
                district_id = district.get("IlceID") or district.get("kod") or district.get("ID")
                if not district_id:
                    print(f"    No district ID found for: {district}")
                    continue
                print(f"    Processing district with ID: {district_id}")
                
                # 4. Fetch District Details
                details = fetch_and_save(f"/ilce-detay/{district_id}", os.path.join(data_dir, f"district_detail_{district_id}.json"))
                
                # 5. Fetch Prayer Times for the District
                prayer_times = fetch_and_save(f"/vakitler/{district_id}", os.path.join(data_dir, f"prayer_times_{district_id}.json"))
            
            # 6. Fetch Bayram Prayer Times for the City ((FOR NOW, NOT!))
            # bayram = fetch_and_save(f"/bayram-namazi/{city_id}", os.path.join(data_dir, f"bayram_{city_id}.json"))

if __name__ == "__main__":
    main()
