#!/bin/python3
import requests
import json

bounds_request = ("https://tankstellenfinder.aral.de/api/v1/locations/within_bounds?sw[]={}&sw[]={}&ne[]={}&ne[]={"
                  "}&autoload=true&travel_mode=driving&avoid_tolls=false&avoid_highways=false&show_stations_on_route"
                  "=true&corridor_radius=5&format=json")

stations = []


def get_bounds(sw1, sw2, ne1, ne2):
    return requests.get(bounds_request.format(sw1, sw2, ne1, ne2)).json()


def get_stations(sw1, sw2, ne1, ne2):
    """Get all locations that have 48 or less gas stations."""
    first_data = get_bounds(sw1, sw2, ne1, ne2)
    for entry in first_data:
        if "size" in entry:
            tmp_sub_data = get_bounds(entry["bounds"]["sw"][0], entry["bounds"]["sw"][1], entry["bounds"]["ne"][0],
                           entry["bounds"]["ne"][1])
            for tmp in tmp_sub_data:
                if "size" in tmp:
                    print(f"getting new stations on bounds {tmp["bounds"]["sw"][0]}, {tmp["bounds"]["sw"][1]}, "
                          f"{tmp["bounds"]["ne"][0]}, {tmp["bounds"]["ne"][1]}")
                    get_stations(tmp["bounds"]["sw"][0], tmp["bounds"]["sw"][1],
                                 tmp["bounds"]["ne"][0], tmp["bounds"]["ne"][1])
                else:
                    print(f"saving station")
                    stations.append(tmp)
        else:
            stations.append(entry)


if __name__ == "__main__":
    # all
    # get_locations(-90, -180, 90, 180)
    # germany
    get_stations(45.1, -4.9, 57.6, 29.2)

    print(f"got {len(stations)} stations")

    unique_objects = []
    seen_ids = set()

    for data in stations:
        """We want to deduplicate all stations here and apply the following filters
        - only german stations
        - only Aral (not BP)"""
        current_id = data["id"]

        if current_id not in seen_ids and data["site_brand"] == "ARAL Tankstelle" and data["country_code"] == "DE":
            unique_objects.append(data)
            seen_ids.add(current_id)

    print(f"got {len(unique_objects)} deduplicated and filtered stations")
    with open("./out/stations_min.json", "w+") as f:
        f.write(json.dumps(unique_objects))

    with open("./out/stations.json", "w+") as f:
        f.write(json.dumps(unique_objects, indent=4))
