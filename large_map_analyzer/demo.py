#!/usr/bin/env python3
from large_map_analyzer import LargeMapAnalyzer
import datetime

# Download complete OSM data for the US from Geofabrik (~11 GB)
# link: https://download.geofabrik.de/north-america.html
input_file = 'us-latest.osm.pbf'
filtered_file = 'motorways.osm.pbf'
output_file = 'motorways.gpkg'
map_analyzer = LargeMapAnalyzer()

# Extract highways using the osmium command
begin_ts = datetime.datetime.now()
map_analyzer.highway_extraction(input_file, filtered_file)
end_ts = datetime.datetime.now()
print(f"Time taken for highway extraction: {end_ts - begin_ts}") # Took ~ 15 minutes for the full US data

# Save the filtered highways to a GeoPackage using geopandas
begin_ts = datetime.datetime.now()
map_analyzer.save_to_geopackage(filtered_file, output_file)
end_ts = datetime.datetime.now()
print(f"Time taken for saving to GeoPackage: {end_ts - begin_ts}") # Took ~ 1 minutes for the full US data