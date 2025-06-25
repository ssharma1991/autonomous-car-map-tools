#!/usr/bin/env python3

from map_analyzer import MapAnalyzer, BoundingBox

# Stanford University area
bbox = BoundingBox(
    left=-122.25,
    bottom=37.4,
    right=-122.1,
    top=37.5
)

print("\nInitializing MapAnalyzer")
road_analyzer = MapAnalyzer()
road_analyzer.add_bounding_box(bbox)

print("\nDownloading road data")
road_analyzer.fetch_road_data()
# road_analyzer.export_for_qgis('road_data.gpkg') # Geopackage can be opened in QGIS

print("\nAnalyzing road data")
road_analyzer.show_road_stats()
road_analyzer.simplify_road_classification()
road_analyzer.plot_interactive_map()
road_analyzer.plot_static_map()