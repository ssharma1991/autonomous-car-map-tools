import plotly.graph_objects as go
import pandas as pd
import requests
import math

class Waypoint:
    def __init__(self, latitude, longitude):
        self.lat = latitude
        self.lon = longitude

class RoutePlotter:
    def __init__(self, waypoints):
        self.waypoints = waypoints
        if len(waypoints) < 2:
            raise ValueError("At least two waypoints are required to plot a route.")
        
    def plot_map(self):
        route = self.generate_route()
        # Create a DataFrame for the waypoints
        df = pd.DataFrame({
            'latitude': [wp.lat for wp in route],
            'longitude': [wp.lon for wp in route]
        })
        # Create a scatter plot using Plotly
        fig = go.Figure()
        fig.add_scattermap(mode='lines+markers', lat=df['latitude'], lon=df['longitude'], marker=dict(size=10, color='blue'))
        center, zoom = self.get_center_zoom(self.waypoints)
        fig.update_layout(title='Route Plot',
                          map= dict(
                              center=dict(lat=center.lat, lon=center.lon),
                              zoom=zoom,
                              style='satellite-streets' # 'basic'/`carto-voyager`, 'open-street-map', 'satellite', 'satellite-streets' 
                          ))
        fig.show()
    
    def get_center_zoom(self, waypoints):
        lat = sum(wp.lat for wp in waypoints) / len(waypoints)
        lon = sum(wp.lon for wp in waypoints) / len(waypoints)
        center = Waypoint(lat, lon)
        zoom = 10  # Default zoom level

        # Calculate zoom level based on the bounding box of the waypoints
        lat_diff = max(wp.lat for wp in waypoints) - min(wp.lat for wp in waypoints)
        lon_diff = max(wp.lon for wp in waypoints) - min(wp.lon for wp in waypoints)
        max_diff = max(lat_diff, lon_diff)
        zoom = math.ceil(math.log(360 / max_diff, 2))
        print("Zoom level set to:", zoom)
        return center, zoom

    def generate_route(self):
        route = []
        for i in range(len(self.waypoints) - 1):
            route.extend(self.generate_route_segment(self.waypoints[i], self.waypoints[i + 1])[:-1]) # skip last point
        route.append(self.waypoints[-1])
        return route

    def generate_route_segment(self, start, end):
        route = self.get_osrm_route(start, end)
        return [Waypoint(lat, lon) for lon, lat in route['routes'][0]['geometry']['coordinates']]
    
    def get_osrm_route(self, start, end):
        url = f"http://router.project-osrm.org/route/v1/driving/{start.lon},{start.lat};{end.lon},{end.lat}?overview=full&geometries=geojson"
        response = requests.get(url)
        return response.json()

if __name__ == "__main__":

    # Example waypoints
    waypoints = [
        Waypoint(37.6130184, -122.39625356),  # near SF airport
        Waypoint(37.4213068, -122.093090),    # near Google
        Waypoint(37.365739, -121.905370)      # near SJ airport
    ]

    # Create a RoutePlotter instance and plot the map
    route_plotter = RoutePlotter(waypoints)
    route_plotter.plot_map()