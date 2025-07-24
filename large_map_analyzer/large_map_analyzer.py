import subprocess
import sys
import osmium
import geopandas
from shapely.geometry import LineString

class LargeMapAnalyzer:
    def __init__(self):
        pass

    def highway_extraction(self, input_file, output_file):
        self.osmium_info(input_file)
        self.extract_highways(input_file, output_file)
        self.osmium_info(output_file)

    def osmium_info(self, file_path):
        try:
            # Runs 'osmium fileinfo <file_path> -e', captures output, and raises error on failure.
            print(subprocess.run(["osmium", "fileinfo", file_path, "-e"], capture_output=True, text=True, check=True).stdout)
        except Exception as e:
            # Catches FileNotFoundError (osmium not found) and CalledProcessError (osmium command failed)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def extract_highways(self, input_file, output_file):
        try:
            # Run 'osmium tags-filter <input_file> highway=motorway,motorway_link -o <output_file> --overwrite'
            print(subprocess.run(
                ["osmium", "tags-filter", input_file, "highway=motorway,motorway_link", "-o", output_file, "--overwrite"],
                check=True
            ).stdout)
        except Exception as e:
            # Catches FileNotFoundError (osmium not found) and CalledProcessError (osmium command failed)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def save_to_geopackage(self, input_file, output_file):
        # Load the filtered highways into a GeoDataFrame
        fp = osmium.FileProcessor(input_file).with_locations()\
            .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
        highway_geometries = []
        for obj in fp:
            try:
                coords = [(n.lon, n.lat) for n in obj.nodes]
                if len(coords) > 1:
                    highway_geometries.append(LineString(coords))
            except osmium.InvalidLocationError:
                pass
        print(f"Extracted {len(highway_geometries)} highway geometries.")

        # Create a GeoDataFrame from the highway geometries
        features = geopandas.GeoDataFrame(geometry=highway_geometries, crs="EPSG:4326")
        print(features.head())
        # features['geometry'] = features['geometry'].simplify(tolerance=0.0001, preserve_topology=True)
        features.to_file(output_file, driver="GPKG")