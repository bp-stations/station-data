#!/bin/python3
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from requests import Session
import json
import os

in_ci = os.getenv("CI") == "true"

print(f"ci status {in_ci}")

bounds_request = (
    "https://tankstellenfinder.aral.de/api/v1/locations/within_bounds?sw[]={}&sw[]={}&ne[]={}&ne[]={"
    "}&autoload=true&travel_mode=driving&avoid_tolls=false&avoid_highways=false&show_stations_on_route"
    "=true&corridor_radius=5&format=json"
)

stations = []
s = Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[403, 502, 503, 504],
    allowed_methods={"GET"},
)
s.mount("https://", HTTPAdapter(max_retries=retries))
s.headers.update(
    {
        "User-Agent": "https://github.com/aral-preise/aral-station-data",
        "Accept": "application/json",
        "Host": "tankstellenfinder.aral.de",
        "Referer": "https://tankstellenfinder.aral.de/?",
    }
)

s.cookies.set("ap-functional", "true", domain=".aral.de")
s.cookies.set("ap-analytics", "false", domain=".aral.de")
s.cookies.set("ap-marketing", "false", domain=".aral.de")


def get_bounds(sw1, sw2, ne1, ne2):
    return s.get(bounds_request.format(sw1, sw2, ne1, ne2)).json()


def get_stations(sw1, sw2, ne1, ne2):
    """Get all locations that have 48 or less gas stations."""
    first_data = get_bounds(sw1, sw2, ne1, ne2)
    for entry in first_data:
        if "size" in entry:
            tmp_sub_data = get_bounds(
                entry["bounds"]["sw"][0],
                entry["bounds"]["sw"][1],
                entry["bounds"]["ne"][0],
                entry["bounds"]["ne"][1],
            )
            for tmp in tmp_sub_data:
                if "size" in tmp:
                    print(
                        f"getting new stations on bounds {tmp["bounds"]["sw"][0]}, {tmp["bounds"]["sw"][1]}, "
                        f"{tmp["bounds"]["ne"][0]}, {tmp["bounds"]["ne"][1]}"
                    )
                    get_stations(
                        tmp["bounds"]["sw"][0],
                        tmp["bounds"]["sw"][1],
                        tmp["bounds"]["ne"][0],
                        tmp["bounds"]["ne"][1],
                    )
                else:
                    if not in_ci:
                        print("saving station")
                    stations.append(tmp)
        else:
            stations.append(entry)


if __name__ == "__main__":
    """Get all locations World Wide"""
    get_stations(-90, -180, 90, 180)

    with open("./out/json/README.md", "w+") as readme:
        readme.writelines(f"""This is the data for BP stations like aral.\n

# Stats\n\r
Total station count: {len(stations)}\n""")
        print(f"got {len(stations)} stations")

        unique_objects = []
        seen_ids = set()

        for data in stations:
            current_id = data["id"]

            if current_id not in seen_ids:
                unique_objects.append(data)
                seen_ids.add(current_id)

        unique_objects = sorted(unique_objects, key=lambda x: x['id'])

        """Worldwide stations"""
        print(f"got {len(unique_objects)} worldwide stations")
        with open("./out/json/all/stations_min.json", "w+") as f:
            f.write(json.dumps(unique_objects))

        with open("./out/json/all/stations.json", "w+") as f:
            f.write(json.dumps(unique_objects, indent=4))

        """Stations by Country found"""
        countries = []
        unique_countries = set()
        for data in stations:
            """Get all countries that exists in stations data"""
            country = data["country_code"]

            if country not in unique_countries:
                countries.append(country)
                unique_countries.add(country)

        print(f"got the following countries: {countries}")
        readme.writelines("""## By Country\n
| Country | Count
| - | - \n""")

        for country in countries:
            """Create files for all countries"""
            tmp_stations = []
            for data in stations:
                if data["country_code"] == country:
                    tmp_stations.append(data)
            tmp_sorted = sorted(tmp_stations, key=lambda x: x['id'])

            print(f"got {len(tmp_stations)} stations for country {country}")
            readme.write(f"| {country} | {len(tmp_stations)}\n")

            with open(f"./out/json/countries/stations_{country}.json", "w+") as f:
                f.write(json.dumps(tmp_sorted, indent=4))

            with open(f"./out/json/countries/stations_{country}_min.json", "w+") as f:
                f.write(json.dumps(tmp_sorted))

        """Stations by Brand found"""
        brands = []
        unique_brands = set()
        for data in stations:
            """Get all countries that exists in stations data"""
            brand = data["site_brand"]

            if brand not in unique_brands:
                brands.append(brand)
                unique_brands.add(brand)

        print(f"got the following brands: {brands}")
        readme.writelines("""## By Brand\n
| Brand | Count
| - | - \n""")

        for brand in brands:
            """Create files for all countries"""
            tmp_stations = []
            for data in stations:
                if data["site_brand"] == brand:
                    tmp_stations.append(data)
            tmp_sorted = sorted(tmp_stations, key=lambda x: x['id'])

            print(f"got {len(tmp_stations)} stations for Brand {brand}")
            readme.write(f"| {brand} | {len(tmp_stations)}\n")

            with open(f"./out/json/brands/stations_{brand}.json", "w+") as f:
                f.write(json.dumps(tmp_sorted, indent=4))

            with open(f"./out/json/brands/stations_{brand}_min.json", "w+") as f:
                f.write(json.dumps(tmp_sorted))
