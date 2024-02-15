# aral-station-data

Generate a JSON list of all [BP](https://www.bp.com/) Gas Stations.

The stations are divided by Brand and Country.

Directory structure:
````commandline
out/
    /all
        /stations.json # these are all BP Stations worldwide
    /brands
        /stations_BP.json # all stations with the Brand BP
        /stations_ARAL Tankstelle.json # all stations from the Brand Aral
    /countries
        /stations_DE.json # all German stations from all brands
        /stations_US.json # all stations in the US from all Brands
    /other # used in another project
````

There is always a ``_min.json`` available that has the whole JSON on a single line.  
Use the default file for better readability.

You can find the data [here](https://github.com/aral-preise/aral-station-data/tree/gh-pages).

There is also a README.md in the data that has basic stats.

# Data accuracy

The data may not be accurate as the script calls the [gas station locator API](https://mein.aral.de/tankstellenfinder/) and this can be prone to errors.  
  
Please note that there may be stations missing!

# Data updated

The data is updated by [this](https://github.com/aral-preise/aral-station-data/blob/main/.github/workflows/generate.yml) GitHub action.  
The version is automatically bumped by [this](https://github.com/aral-preise/aral-station-data/blob/main/.github/workflows/version.yml) GitHub action on cron '0 2 * * 1'.