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


x=client.d1.database.list(account_id=os.getenv("CF_ACCOUNT_ID"))

station_path = (
    Path(__file__)
    .parent.absolute()
    .joinpath("./out/json/brands/stations_ARAL Tankstelle_min.json")
)

def export_stations():
    station_data = load_json(station_path)
    tmp_statements = ["DELETE FROM stations;"]
    for station in station_data:
        # FIXME: the should be a better way for this
        tmp_statements.append("INSERT INTO stations (id,name,lat,lng,address,city,state,postcode,"
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
    client.d1.database.query(account_id=os.getenv("CF_ACCOUNT_ID"), database_id=os.getenv("CF_DATABASE_ID"), sql="".join(tmp_statements))


if __name__ == "__main__":
    export_stations()
