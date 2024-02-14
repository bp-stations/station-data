#!/bin/python3
from datetime import datetime
from pathlib import Path
from json import load, dumps
import argparse
import sqlite3


def load_json(file):
    f = open(file, encoding="utf8")
    return load(f)


station_path = Path(__file__).parent.absolute().joinpath('./out/stations_min.json')
output_path = Path(__file__).parent.absolute().joinpath('./out/aral.db')

station_query = ("CREATE TABLE IF NOT EXISTS `stations`(id INTEGER PRIMARY KEY, name TEXT NOT NULL, lat FLOAT NOT "
                 "NULL, lng FLOAT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, state TEXT, postcode INTEGER "
                 "NOT NULL, country_code TEXT NOT NULL, telephone TEXT NOT NULL, site_brand TEXT NOT NULL, "
                 "watchlist_id INTEGER NOT NULL, website TEXT NOT NULL, fuel TEXT NOT NULL, facilities TEXT NOT NULL);")
fuel_query = "CREATE TABLE IF NOT EXISTS `fuel`(id INTEGER PRIMARY KEY, name TEXT NOT NULL);"
facilities_query = "CREATE TABLE IF NOT EXISTS `facilities`(id INTEGER PRIMARY KEY, name TEXT NOT NULL);"

connection = sqlite3.connect(output_path)
cursor = connection.cursor()

cursor.execute(station_query)
cursor.execute(fuel_query)
cursor.execute(facilities_query)

connection.commit()


def export_facilities():
    station_data = load_json(station_path)
    unique_facilities = []
    for station in station_data:
        for facility in station["facilities"]:
            if facility not in unique_facilities:
                unique_facilities.append(facility)
                cursor.execute("INSERT INTO facilities (name) VALUES(?)", (facility,))


def export_fuel():
    station_data = load_json(station_path)
    unique_fuel = []
    for station in station_data:
        for fuel in station["products"]:
            if fuel not in unique_fuel:
                unique_fuel.append(fuel)
                cursor.execute("INSERT INTO fuel (name) VALUES(?)", (fuel,))


def export_stations():
    station_data = load_json(station_path)
    for station in station_data:
        try:
            cursor.execute(
                "INSERT INTO stations (id,name,lat,lng,address,city,state,postcode,country_code,telephone,site_brand,"
                "watchlist_id,website,fuel,facilities) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                (
                    station["id"],
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
                    ', '.join(station["products"]),
                    ', '.join(station["facilities"])
                ))
        except sqlite3.IntegrityError:
            print(f"error while inserting {station['id']}")


if __name__ == "__main__":
    export_facilities()
    export_fuel()
    export_stations()
    connection.commit()
