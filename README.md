<h3 align="center">Station Data</h3>

<div align="center">

  [![Status](https://img.shields.io/badge/status-active-success.svg)]() 
  [![License](https://img.shields.io/github/license/bp-stations/station-data)](/LICENSE)
  [![Last data release](https://img.shields.io/github/release-date/bp-stations/station-data)]()

</div>

---

<p align="center"> This is the data fetcher for all <a href="https://www.bp.com/">BP</a> gas stations.
    <br> 
</p>

## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [Affiliation](#affiliation)

## 🧐 About <a name = "about"></a>
This program is fetching all [BP](https://www.bp.com/) gas stations from the [Aral](https://www.aral.de/) "tankstellenfinder" api.
The data is saved in the following formats: ``json`` and ``ov2``.

## 🏁 Getting Started <a name = "getting_started"></a>
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites
What things you need to install the software and how to install them.

``python3`` is required.

### Installing

Install the required packages by running:

```
pip install -r requirements.txt
```

## 🎈 Usage <a name="usage"></a>
You can now run the data fetcher with ``python main.py``

The data will be saved in ``./out/json`` and ``./out/ov2``.

### Program structure:

````commandline
/
    /main.py # gets all stations and automatically sorts them in /out
    /generator.py # generates the following files in /out/other: sitemap.xml, facilities.json and fuel.json
    /database.py # generates a sqlite3 file based on "stations_ARAL Tankstelle_min.json" which is used in "aral-prices"
````

### Directory structure:
````commandline
out/
    /json
        /all
            /stations.json # these are all BP Stations worldwide
        /brands
            /stations_BP.json # all stations with the Brand BP
            /stations_ARAL Tankstelle.json # all stations from the Brand Aral
        /countries
            /stations_DE.json # all German stations from all brands
            /stations_US.json # all stations in the US from all Brands
        /other # used in another project
    /ov2 # 
        /all
            /stations.ov2 # these are all BP Stations worldwide
        /brands
            /stations_BP.ov2 # all stations with the Brand BP
            /stations_ARAL Tankstelle.ov2 # all stations from the Brand Aral
        /countries
            /stations_DE.ov2 # all German stations from all brands
            /stations_US.ov2 # all stations in the US from all Brands
````

There is always a ``_min.json`` available (e.g. `stations_min.json`) that has the whole JSON on a single line.  
Use the default file for better readability.

The ``.ov2`` files have skipper records, so performance should be good.

You can find the data [here](https://github.com/bp-stations/station-data/tree/gh-pages).

There is also a [README.md](https://github.com/bp-stations/station-data/tree/gh-pages/json/README.md) in the data that has basic stats.

### Data accuracy

The data may not be accurate as the script calls the [gas station locator API](https://mein.aral.de/tankstellenfinder/) and this can be prone to errors.  
  
Please note that there may be stations missing!

## 🚀 Deployment <a name = "deployment"></a>
You can see a example deployment at [./.github/workflows/generate.yml](./.github/workflows/generate.yml)

### Cron

The data is updated by [this](./.github/workflows/generate.yml) GitHub action.  
The version is automatically bumped by [this](https://github.com/bp-stations/station-data/blob/main/.github/workflows/version.yml) GitHub action on cron '0 2 * * 1'.

## Style
The code is formatted and checked with [ruff](https://github.com/astral-sh/ruff)s default settings.

## ⛏️ Built Using <a name = "built_using"></a>
None

## Affiliation <a name = "affiliation"></a>
I am not affiliated with the Aral Aktiengesellschaft nor the BP p.l.c.
