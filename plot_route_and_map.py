import osm_tile_manager
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

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

class MapPlotter:
    def __init__(self):
        self.zoom = 10 # Larger number = more detail
        self.osm_obj = osm_tile_manager.OSMTileManager()

    def plot_map(self, waypoints):
        map = self.get_map(waypoints)
        bb = BoundingBox(waypoints)
        tile_top_left_num = self.osm_obj.deg2tilenum(bb.get_top_left().lat, bb.get_top_left().lon, self.zoom)
        tile_top_left_lat, tile_top_left_lon = self.osm_obj.tilenum2deg(tile_top_left_num[0], tile_top_left_num[1], self.zoom)
        tile_bottom_right_num = self.osm_obj.deg2tilenum(bb.get_bottom_right().lat, bb.get_bottom_right().lon, self.zoom)
        tile_bottom_right_lat, tile_bottom_right_lon = self.osm_obj.tilenum2deg(tile_bottom_right_num[0]+1, tile_bottom_right_num[1]+1, self.zoom)
        plt.imshow(map, extent=[tile_top_left_lon, tile_bottom_right_lon, tile_bottom_right_lat, tile_top_left_lat])

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
    
    def plot_route(self, waypoints):
        route = self.generate_route(waypoints)
        lats = [wp.lat for wp in route]
        lons = [wp.lon for wp in route]
        plt.plot(lons, lats)

    def generate_route(self, waypoints):
        route = []
        for i in range(len(waypoints) - 1):
            route.extend(self.generate_route_segment(waypoints[i], waypoints[i + 1])[:-1])
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
    RoutePlotter().plot_route(waypoints)
    MapPlotter().plot_map(waypoints)
    plt.show()