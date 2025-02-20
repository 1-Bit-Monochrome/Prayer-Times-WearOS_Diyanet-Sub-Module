import os
import json

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Determine the repository root.
    # If this script is in a subfolder (e.g., "scripts"), then repo_root is one level up.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    target_data_dir = os.path.join(repo_root, "data")
    os.makedirs(target_data_dir, exist_ok=True)
    
    countries_file = os.path.join(target_data_dir, "countries.json")
    
    if not os.path.exists(countries_file):
        print("countries.json not found in the data folder.")
        return

    countries = load_json(countries_file)
    manifest = {"countries": []}

    for country in countries:
        ulke_id = country.get("UlkeID")
        if not ulke_id:
            continue
        
        country_entry = {
            "UlkeID": ulke_id,
            "UlkeAdi": country.get("UlkeAdi"),
            "UlkeAdiEn": country.get("UlkeAdiEn"),
            "cities": []  # This will be populated below.
        }

        # Load the cities file for this country.
        cities_file = os.path.join(target_data_dir, f"cities_{ulke_id}.json")
        if os.path.exists(cities_file):
            cities = load_json(cities_file)
            for city in cities:
                sehir_id = city.get("SehirID")
                if not sehir_id:
                    continue

                # For each city, add pointers to its districts and bayram data.
                city_entry = {
                    "SehirID": sehir_id,
                    "SehirAdi": city.get("SehirAdi"),
                    "SehirAdiEn": city.get("SehirAdiEn"),
                    "districts_file": f"districts_{sehir_id}.json",
                    "bayram_file": f"bayram_{sehir_id}.json"
                }
                country_entry["cities"].append(city_entry)
        else:
            print(f"Cities file for country {ulke_id} not found.")
        
        manifest["countries"].append(country_entry)

    # Save the manifest file.
    manifest_file = os.path.join(target_data_dir, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Manifest created: {manifest_file}")

if __name__ == "__main__":
    main()