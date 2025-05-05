from road_analyzer import RoadAnalyzer, BoundingBox

# Stanford University area
bbox = BoundingBox(
    left=-122.25,
    bottom=37.4,
    right=-122.1,
    top=37.5
)

print("\nInitializing RoadAnalyzer")
road_analyzer = RoadAnalyzer()
road_analyzer.add_bounding_box(bbox)

print("\nDownloading road data")
road_analyzer.fetch_road_data()
# road_analyzer.export_for_qgis('road_data.gpkg') # Geopackage can be opened in QGIS

print("\nAnalyzing road data")
road_analyzer.show_road_stats()
road_analyzer.classify_road_for_adas()
# road_analyzer.plot_graph()
road_analyzer.plot_graph_with_background_map()
