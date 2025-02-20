import requests
import os
import json

BASE_URL = "https://ezanvakti.emushaf.net"

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
            print(f" item keys: {list(data[0].keys())}")
    else:
        print(f"[INVALID] {name}: Unexpected JSON type {type(data)}")

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved data to {filename}")

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_and_save(endpoint, filename, force_refresh=False):
    if not force_refresh and os.path.exists(filename):
        print(f"Skipping {filename} (already exists)")
        return load_json(filename)
    data = fetch_json(endpoint)
    if data:
        save_json(filename, data)
    return data

def main(force_refresh=False):
    os.makedirs("data", exist_ok=True)
    
    master_data = {"countries": []}
    
    # 1. Fetch Countries
    countries = fetch_and_save("/ulkeler", "data/countries.json", force_refresh)
    if not countries:
        print("No countries data.")
        return
    for country in countries:
        country_id = country.get("UlkeID")
        if not country_id:
            continue
        print(f"Processing country: {country.get('UlkeAdiEn', country.get('UlkeAdi'))} (ID: {country_id})")
        country_entry = {
            "UlkeAdi": country.get("UlkeAdi"),
            "UlkeAdiEn": country.get("UlkeAdiEn"),
            "UlkeID": country_id,
            "cities": []
        }
        
        # 2. Fetch Cities for the Country
        cities = fetch_and_save(f"/sehirler/{country_id}", f"data/cities_{country_id}.json", force_refresh)
        if not cities:
            master_data["countries"].append(country_entry)
            continue
        
        for city in cities:
            city_id = city.get("SehirID")
            if not city_id:
                continue
            print(f"  Processing city: {city.get('SehirAdiEn', city.get('SehirAdi'))} (ID: {city_id})")
            city_entry = {
                "SehirAdi": city.get("SehirAdi"),
                "SehirAdiEn": city.get("SehirAdiEn"),
                "SehirID": city_id,
                "districts": [],
                "bayram": None
            }
            
            # 3. Fetch Districts for the City
            districts = fetch_and_save(f"/ilceler/{city_id}", f"data/districts_{city_id}.json", force_refresh)
            if districts:
                for district in districts:
                    # Trying different keys for district ID
                    district_id = district.get("IlceID") or district.get("kod") or district.get("ID")
                    if not district_id:
                        print(f"    No district ID found for: {district}")
                        continue
                    print(f"    Processing district (ID: {district_id})")
                    
                    # 4. Fetch District Details
                    details = fetch_and_save(f"/ilce-detay/{district_id}", f"data/district_detail_{district_id}.json", force_refresh)
                    
                    # 5. Fetch Prayer Times for the District
                    prayer_times = fetch_and_save(f"/vakitler/{district_id}", f"data/prayer_times_{district_id}.json", force_refresh)
                    
                    district_entry = {
                        "district": district,  # here the original district info
                        "details": details,
                        "prayer_times": prayer_times
                    }
                    city_entry["districts"].append(district_entry)
            
            # 6. Fetch Bayram Prayer Times for the City (Beta, Not included for now)
            bayram = fetch_and_save(f"/bayram-namazi/{city_id}", f"data/bayram_{city_id}.json", force_refresh)
            city_entry["bayram"] = bayram
            
            country_entry["cities"].append(city_entry)
        
        master_data["countries"].append(country_entry)
    
    # Save entire hierarchical data into one master JSON file
    save_json("data/master_data.json", master_data)
    print("Master data compilation complete.")

if __name__ == "__main__":
    # Set force_refresh=True if we want to ignore existing files and re-fetch all data.
    main(force_refresh=False)