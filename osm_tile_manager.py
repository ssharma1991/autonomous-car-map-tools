import os
from random import uniform  
from time import sleep 
import requests
import math
from io import BytesIO
from PIL import Image

class OSMTileManager:
    def __init__(self):
        # Create a directory to store the tiles
        self.cache_path = "osm_tiles"
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)
    
    def get_tile(self, xtile, ytile, zoom):
        # Download and cache the tile if it doesn't exist
        path = self.cache_path + f"/{zoom}_{xtile}_{ytile}.png"
        if not os.path.exists(path):
            tile = self.download_tile(xtile, ytile, zoom)
            with open(path, "wb") as f:
                f.write(tile)

        # Read the tile from the cache
        with open(path, "rb") as f:
                tile = f.read()
        tile = Image.open(BytesIO(tile))
        return tile
    
    def download_tile(self, xtile, ytile, zoom):
        url = f"https://a.tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png"
        print(f"Downloading {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    
    # Ref: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
    def deg2tilenum(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def tilenum2deg(self, xtile, ytile, zoom):
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)
    
    def get_osrm_route(self, start, end):
        url = f"http://router.project-osrm.org/route/v1/driving/{start.lon},{start.lat};{end.lon},{end.lat}?overview=full&geometries=geojson"
        response = requests.get(url)
        return response.json()
    