import osm_tile_manager
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from PIL import Image
import math

class Waypoint:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

class BoundingBox:
    def __init__(self, min_lat, min_lon, max_lat, max_lon):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon

    def __init__(self, waypoints):
        self.min_lat = min([wp.lat for wp in waypoints])
        self.min_lon = min([wp.lon for wp in waypoints])
        self.max_lat = max([wp.lat for wp in waypoints])
        self.max_lon = max([wp.lon for wp in waypoints])
    
    def get_top_left(self):
        return Waypoint(self.max_lat, self.min_lon)

    def get_bottom_right(self):
        return Waypoint(self.min_lat, self.max_lon)

    def get_bottom_left(self):
        return Waypoint(self.min_lat, self.min_lon)

    def get_top_right(self):
        return Waypoint(self.max_lat, self.max_lon)

class MapPlotter:
    def __init__(self):
        self.zoom = 10 # Larger number = more detail
        self.osm_obj = osm_tile_manager.OSMTileManager()

    def set_zoom(self, waypoints):
        # Select zoom 0-19 based on the bounding box of the waypoints
        bounding_box = BoundingBox(waypoints)
        lat_diff = bounding_box.max_lat - bounding_box.min_lat
        lon_diff = bounding_box.max_lon - bounding_box.min_lon
        max_diff = max(lat_diff, lon_diff)

        # Ref: https://wiki.openstreetmap.org/wiki/Zoom_levels
        self.zoom = math.ceil(math.log(360 / max_diff, 2)) + 1
        if self.zoom < 0:
            self.zoom = 0
        elif self.zoom > 19:
            self.zoom = 19
        print("Auto zoom level set to:", self.zoom)

    def plot_map(self, waypoints):
        self.set_zoom(waypoints)
        map = self.get_map(waypoints)
        bb = BoundingBox(waypoints)
        tile_bottom_left_num = self.osm_obj.deg2tilenum(bb.get_bottom_left().lat, bb.get_bottom_left().lon, self.zoom)
        tile_bottom_left_lat, tile_bottom_left_lon = self.osm_obj.tilenum2deg(tile_bottom_left_num[0], tile_bottom_left_num[1]+1, self.zoom)
        tile_top_right_num = self.osm_obj.deg2tilenum(bb.get_top_right().lat, bb.get_top_right().lon, self.zoom)
        tile_top_right_lat, tile_top_right_lon = self.osm_obj.tilenum2deg(tile_top_right_num[0]+1, tile_top_right_num[1], self.zoom)
        plt.figure()
        plt.title("Route and Map")
        m = Basemap(projection='merc',llcrnrlat=tile_bottom_left_lat,urcrnrlat=tile_top_right_lat,\
            llcrnrlon=tile_bottom_left_lon,urcrnrlon=tile_top_right_lon, ax=plt.gca(), resolution='h', area_thresh=1000)
        m.drawcoastlines()
        m.imshow(map, interpolation='lanczos', origin='upper')
        return m

    def get_map(self, waypoints):
        bounding_box = BoundingBox(waypoints)
        return self.get_map_bb(bounding_box)

    def get_map_bb(self, bounding_box):
        top_left = bounding_box.get_top_left()
        top_left_tile_num = self.osm_obj.deg2tilenum(top_left.lat, top_left.lon, self.zoom)
        min_x, min_y = top_left_tile_num
        bottom_right = bounding_box.get_bottom_right()
        bottom_right_tile_num = self.osm_obj.deg2tilenum(bottom_right.lat, bottom_right.lon, self.zoom)
        max_x, max_y = bottom_right_tile_num
        img = None

        for x in range(min_x, max_x + 1):
            col_img = None
            for y in range(min_y, max_y + 1):
                tile = self.osm_obj.get_tile(x, y, self.zoom)
                if tile.mode == 'P':
                    tile = tile.convert('RGB')
                tile = np.array(tile)
                tile = Image.fromarray(tile)

                if col_img is None:
                    col_img = tile
                else:
                    col_img = np.concatenate((col_img, tile), axis=0)
            if img is None:
                img = col_img
            else:
                img = np.concatenate((img, col_img), axis=1)
        return img

class RoutePlotter:
    def __init__(self):
        self.osm_obj = osm_tile_manager.OSMTileManager()
    
    def plot_route(self, waypoints, base_map):
        route = self.generate_route(waypoints)
        lats = [wp.lat for wp in route]
        lons = [wp.lon for wp in route]
        x, y = base_map(lons, lats)
        base_map.plot(x, y, marker='o', color='b', markersize=4, linewidth=1)

    def generate_route(self, waypoints):
        route = []
        for i in range(len(waypoints) - 1):
            route.extend(self.generate_route_segment(waypoints[i], waypoints[i + 1])[:-1]) # skip last point
        route.append(waypoints[-1])
        return route

    def generate_route_segment(self, start, end):
        route = self.osm_obj.get_osrm_route(start, end)
        return [Waypoint(lat, lon) for lon, lat in route['routes'][0]['geometry']['coordinates']]

if __name__ == "__main__":
    waypoints = [
        Waypoint(37.6130184, -122.39625356),  # near SF airport
        Waypoint(37.4213068, -122.093090),    # near Google
        Waypoint(37.365739, -121.905370)      # near SJ airport
    ]
    base_map = MapPlotter().plot_map(waypoints)
    RoutePlotter().plot_route(waypoints, base_map)
    plt.show()