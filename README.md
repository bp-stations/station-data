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