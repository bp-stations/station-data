#!/usr/bin/env python3
from cloudflare import Cloudflare
from pathlib import Path
from json import load
import os

client = Cloudflare(
    api_token=os.getenv("CF_API_TOKEN")
)

def load_json(file):
    f = open(file, encoding="utf8")
    return load(f)

station_path = (
    Path(__file__)
    .parent.absolute()
    .joinpath("./out/json/brands/stations_ARAL Tankstelle_min.json")
)

def export_stations():
    station_data = load_json(station_path)
    tmp_lists = []
    tmp_list = []
    counter = 0
    for station in station_data:
        # FIXME: the should be a better way for this
        tmp_list.append("INSERT INTO stations (id,name,lat,lng,address,city,state,postcode,"
                             "country_code,telephone,site_brand,watchlist_id,website,fuel,facilities) "
                             "VALUES ({},\"{}\",{},{},\"{}\",\"{}\",\"{}\",{},\"{}\",\"{}\",\"{}\",{},\"{}\",\"{}\",\"{}\");".format(station["watchlist_id"],
        station["name"],
        station["lat"],
        station["lng"],
        station["address"],
        station["city"],
        station["state"],
        station["postcode"],
        station["country_code"],
        station["telephone"],
        station["site_brand"],
        station["watchlist_id"],
        station["website"],
        ", ".join(station["products"]),
        ", ".join(station["facilities"])))
        counter = counter + 1
        if len(tmp_list) > 98:
            tmp_lists.append(tmp_list)
            tmp_list = []
            counter = 0

    querys = ["DELETE FROM stations;"]
    tmp_query = []
    for entry in tmp_lists:
        for station in entry:
            tmp_query.append(station)
        querys.append("".join(tmp_query))
        tmp_query = []
    for query in querys:
        client.d1.database.query(account_id=os.getenv("CF_ACCOUNT_ID"), database_id=os.getenv("CF_DATABASE_ID"), sql=query)


if __name__ == "__main__":
    export_stations()
