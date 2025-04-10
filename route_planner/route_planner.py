from osm_handler import OSMHandler
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from PIL import Image
import math
import plotly.graph_objects as go
import pandas as pd

class Waypoint:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

class BoundingBox:
    def __init__(self, waypoints):
        self.min_lat = min(wp.lat for wp in waypoints)
        self.min_lon = min(wp.lon for wp in waypoints)
        self.max_lat = max(wp.lat for wp in waypoints)
        self.max_lon = max(wp.lon for wp in waypoints)
    
    def get_top_left(self):
        return Waypoint(self.max_lat, self.min_lon)

    def get_bottom_right(self):
        return Waypoint(self.min_lat, self.max_lon)

    def get_bottom_left(self):
        return Waypoint(self.min_lat, self.min_lon)

    def get_top_right(self):
        return Waypoint(self.max_lat, self.max_lon)

class RoutePlanner:
    def __init__(self):
        self.waypoints = None
        self.bounding_box = None
        self.route = None
        self.zoom = None
        self.osm_obj = OSMHandler()
        self.basemap_obj = None

    def add_waypoints(self, waypoints):
        self.waypoints = waypoints
        if len(waypoints) < 2:
            raise ValueError("At least two waypoints are required to plot a route.")
        self.bounding_box = BoundingBox(waypoints)

    def calculate_route(self):
        route = []
        for i in range(len(self.waypoints) - 1):
            route.extend(self.__generate_route_segment(self.waypoints[i], self.waypoints[i + 1])[:-1]) # skip last point
        route.append(self.waypoints[-1])
        self.route = route

    def __generate_route_segment(self, start, end):
        route = self.osm_obj.get_osrm_route(start, end)
        return [Waypoint(lat, lon) for lon, lat in route['routes'][0]['geometry']['coordinates']]

    def plot_static_map(self, zoom=None):
        if self.waypoints is None:
            raise ValueError("No waypoints added. Please add waypoints before plotting the map.")
        if self.route is None:
            print("WARNING: No route calculated. Please calculate the route before plotting.")
        
        # Set Zoom level
        if zoom is None:
            self.__set_zoom_static_map()
        else:
            if zoom < 0 or zoom > 19:
                raise ValueError("Zoom level must be between 0 and 19.")
            self.zoom = zoom
        print("Zoom level set to:", self.zoom)

        # Plot map
        map_raster = self.__get_stitched_map()
        bb = self.bounding_box
        tile_bottom_left_num = self.osm_obj.deg2tilenum(bb.get_bottom_left().lat, bb.get_bottom_left().lon, self.zoom)
        tile_bottom_left_lat, tile_bottom_left_lon = self.osm_obj.tilenum2deg(tile_bottom_left_num[0], tile_bottom_left_num[1]+1, self.zoom)
        tile_top_right_num = self.osm_obj.deg2tilenum(bb.get_top_right().lat, bb.get_top_right().lon, self.zoom)
        tile_top_right_lat, tile_top_right_lon = self.osm_obj.tilenum2deg(tile_top_right_num[0]+1, tile_top_right_num[1], self.zoom)
        plt.figure()
        plt.title("Route and Map")
        self.basemap_obj = Basemap(projection='merc',llcrnrlat=tile_bottom_left_lat,urcrnrlat=tile_top_right_lat,\
            llcrnrlon=tile_bottom_left_lon,urcrnrlon=tile_top_right_lon, ax=plt.gca(), resolution='h', area_thresh=1000)
        self.basemap_obj.drawcoastlines()
        self.basemap_obj.imshow(map_raster, interpolation='lanczos', origin='upper')

        # Plot waypoints
        lats = [wp.lat for wp in self.waypoints]
        lons = [wp.lon for wp in self.waypoints]
        x, y = self.basemap_obj(lons, lats)
        self.basemap_obj.plot(x, y, marker='o', color='r', markersize=8, linewidth=0, label='Waypoints')

        # Plot route
        if self.route:
            lats = [wp.lat for wp in self.route]
            lons = [wp.lon for wp in self.route]
            x, y = self.basemap_obj(lons, lats)
            self.basemap_obj.plot(x, y, marker='o', color='b', markersize=4, linewidth=1, label='Route')

        plt.legend()
        plt.tight_layout()
        plt.show()

    def __set_zoom_static_map(self):
        # Select zoom 0-19 based on the bounding box of the waypoints
        # Higher zoom value means more detail
        lat_diff = self.bounding_box.max_lat - self.bounding_box.min_lat
        lon_diff = self.bounding_box.max_lon - self.bounding_box.min_lon
        max_diff = max(lat_diff, lon_diff)

        # Ref: https://wiki.openstreetmap.org/wiki/Zoom_levels
        self.zoom = math.ceil(math.log(360 / max_diff, 2)) + 1
        if self.zoom < 0:
            self.zoom = 0
        elif self.zoom > 19:
            self.zoom = 19
    
    def __get_stitched_map(self):
        top_left = self.bounding_box.get_top_left()
        top_left_tile_num = self.osm_obj.deg2tilenum(top_left.lat, top_left.lon, self.zoom)
        min_x, min_y = top_left_tile_num
        bottom_right = self.bounding_box.get_bottom_right()
        bottom_right_tile_num = self.osm_obj.deg2tilenum(bottom_right.lat, bottom_right.lon, self.zoom)
        max_x, max_y = bottom_right_tile_num

        tile_width, tile_height = 256, 256
        stitched_width = (max_x - min_x + 1) * tile_width
        stitched_height = (max_y - min_y + 1) * tile_height
        stitched_map = Image.new('RGB', (stitched_width, stitched_height))

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile = self.osm_obj.get_tile(x, y, self.zoom)
                if tile.mode == 'P':
                    tile = tile.convert('RGB')
                stitched_map.paste(tile, ((x - min_x) * tile_width, (y - min_y) * tile_height))

        return stitched_map

    def plot_interactive_map(self):
        if self.waypoints is None:
            raise ValueError("No waypoints added. Please add waypoints before plotting the map.")
        if self.route is None:
            print("WARNING: No route calculated. Please calculate the route before plotting.")
        
        # Set Zoom level and center
        self.__set_zoom_interactive_map()
        lat = sum(wp.lat for wp in self.waypoints) / len(self.waypoints)
        lon = sum(wp.lon for wp in self.waypoints) / len(self.waypoints)
        center = Waypoint(lat, lon)

        # Plot map using Plotly
        fig = go.Figure()
        fig.update_layout(title='Route Plot',
                          map=dict(
                              center=dict(lat=center.lat, lon=center.lon),
                              zoom=self.zoom,
                              style='basic' # 'basic'/`carto-voyager`, 'open-street-map', 'satellite', 'satellite-streets' 
                            ),
                          updatemenus=[
                            dict(
                                type='buttons',
                                buttons=[
                                    dict(label='Basic', method='relayout', args=['map.style', 'basic']),
                                    dict(label='Satellite', method='relayout', args=['map.style', 'satellite']),
                                    dict(label='Satellite Streets', method='relayout', args=['map.style', 'satellite-streets']),
                                    dict(label='Open Street Map', method='relayout', args=['map.style', 'open-street-map'])
                                ]
                            )
                          ]
                        )
        
        # Plot waypoints
        df = pd.DataFrame({
            'latitude': [wp.lat for wp in self.waypoints],
            'longitude': [wp.lon for wp in self.waypoints]
        })
        fig.add_scattermap(mode='markers', lat=df['latitude'], lon=df['longitude'], marker=dict(size=20, color='red'), name='Waypoints')

        # Plot route
        if self.route:
            df = pd.DataFrame({
                'latitude': [wp.lat for wp in self.route],
                'longitude': [wp.lon for wp in self.route]
            })
            fig.add_scattermap(mode='lines+markers', lat=df['latitude'], lon=df['longitude'], marker=dict(size=10, color='blue'), name='Route')
        
        fig.show()

    def __set_zoom_interactive_map(self):
        self.__set_zoom_static_map()
        self.zoom = self.zoom - 1