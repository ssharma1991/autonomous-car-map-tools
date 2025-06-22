import plotly.graph_objects as go
import pandas as pd
import osmnx as ox
import numpy as np
import networkx as nx

class MapEngine:
    def __init__(self):
        self.latlong = []
        self.time = []
        self.bounding_box = None
        self.osm_graph = None
        self.ego_map = None

    def set_gnss_data(self, path):
        # Load the data
        gnss_data = pd.read_csv(path)

        # Subsample the dataframe
        time_delta_s  = gnss_data['timestamp_s'][1] - gnss_data['timestamp_s'][0]
        if time_delta_s < 1:
            freq = int(1/time_delta_s)
            gnss_data = gnss_data.iloc[::freq].reset_index(drop=True)

        # Extract latitude, longitude, and time
        self.latlong = gnss_data[['latitude_deg', 'longitude_deg']].values.tolist()
        self.time = (gnss_data['timestamp_s'] - gnss_data['timestamp_s'].min()).round(1).values.tolist()

        # Calculate bounding box
        latitudes = [lat for lat, lon in self.latlong]
        longitudes = [lon for lat, lon in self.latlong]
        self.bounding_box = {
            'left': min(longitudes),
            'bottom': min(latitudes),
            'right': max(longitudes),
            'top': max(latitudes)
        }

        # Fetch the OSM graph for the bounding box
        highway_types = ['motorway', 'motorway_link']
        self.osm_graph = ox.graph.graph_from_bbox(
            bbox=(self.bounding_box['left'], self.bounding_box['bottom'], self.bounding_box['right'], self.bounding_box['top']),
            network_type='drive',
            simplify=False,
            retain_all=True,
            custom_filter=f'["highway"~"{ "|".join(highway_types) }"]'
        )
        self.osm_graph = ox.distance.add_edge_lengths(self.osm_graph)
        print(f"OSM graph fetched with {len(self.osm_graph.nodes)} nodes and {len(self.osm_graph.edges)} edges.")

    def calculate_realtime_map(self):
        self.ego_map = []
        for latlong in self.latlong:
            print(f"Processing GNSS position: {latlong} at index {self.latlong.index(latlong)}")
            ego_graph = self.get_map_at_latlong(latlong)
            self.ego_map.append(ego_graph)

    def get_map_at_latlong(self, latlong):
        FORWARD_DISTANCE_THRESHOLD = 500  # meters
        BACKWARD_DISTANCE_THRESHOLD = 100
        # print("latlong:", latlong)

        # Map matching
            # Find ego_edge: the edge closest to the current position
            # Find ego_pose: nearest point on the edge to GNSS position
            # Find distance to next node
            # Find distance to previous node
        ego_edge, dist = ox.distance.nearest_edges(
            self.osm_graph,
            X=latlong[1],  # longitude
            Y=latlong[0],  # latitude
            return_dist=True
        )
        # print(f"Ego edge found: {ego_edge}, Distance to edge: {dist} meters")
        forward_node_id = ego_edge[1]  # The node at the end of the edge
        forward_node_data = self.osm_graph.nodes[forward_node_id]  # The node at the end of the edge
        forward_latlon = forward_node_data['y'], forward_node_data['x']
        backward_node_id = ego_edge[0]  # The node at the start of the edge
        backward_node_data = self.osm_graph.nodes[backward_node_id]  # The node at the start of the edge
        backward_latlon = backward_node_data['y'], backward_node_data['x']

        ego_pose = self.closest_point_on_line(forward_latlon, backward_latlon, latlong)
        # print(f"Ego pose: {ego_pose}")

        forward_node_dist = ox.distance.great_circle(forward_latlon[0], forward_latlon[1], ego_pose[0], ego_pose[1])
        backward_node_dist = ox.distance.great_circle(backward_latlon[0], backward_latlon[1], ego_pose[0], ego_pose[1])
        # print(f"Forward node distance: {forward_node_dist}, Backward node distance: {backward_node_dist}")

        edge_length = self.osm_graph.edges[ego_edge]['length']
        # print(f"Edge length: {edge_length} meters")


        # Calculate horizon
            # Create empty ego_graph
            # Add ego_edge
            # Add forward edges upto 500m
            # Add backward edges upto 100m
        ego_graph = nx.MultiDiGraph()
        nodes = [{'id': forward_node_id, 'dist': forward_node_dist, 'direction': 'forward'},
                 {'id': backward_node_id, 'dist': backward_node_dist, 'direction': 'backward'}]
        ego_graph.add_node(ego_edge[0], **backward_node_data)
        ego_graph.add_node(ego_edge[1], **forward_node_data)
        default_color = 0
        ego_graph.add_edge(ego_edge[0], ego_edge[1], default_color, **self.osm_graph.edges[ego_edge])

        while nodes:
            current_node = nodes.pop(0)
            current_id = current_node['id']
            current_dist = current_node['dist']
            current_direction = current_node['direction']

            if current_direction == 'forward' and current_dist < FORWARD_DISTANCE_THRESHOLD:
                # Forward direction: add neighbors
                for neighbor in self.osm_graph.neighbors(current_id):
                    # Check if the neighbor is already in the ego_graph
                    if neighbor in ego_graph.nodes:
                        continue
                    neighbor_data = self.osm_graph.nodes[neighbor]
                    edge_id = (current_id, neighbor, default_color)
                    edge_data = self.osm_graph.edges[edge_id]
                    ego_graph.add_node(neighbor, **neighbor_data)
                    ego_graph.add_edge(current_id, neighbor, default_color, **edge_data)
                    nodes.append({'id': neighbor, 'dist': current_dist + edge_data['length'], 'direction': 'forward'})
            elif current_direction == 'backward' and current_dist < BACKWARD_DISTANCE_THRESHOLD:
                # Backward direction: add neighbors
                for neighbor in self.osm_graph.predecessors(current_id):
                    # Check if the neighbor is already in the ego_graph
                    if neighbor in ego_graph.nodes:
                        continue

                    neighbor_data = self.osm_graph.nodes[neighbor]
                    edge_id = (neighbor, current_id, default_color)
                    edge_data = self.osm_graph.edges[edge_id]
                    ego_graph.add_node(neighbor, **neighbor_data)
                    ego_graph.add_edge(neighbor, current_id, default_color, **edge_data)
                    nodes.append({'id': neighbor, 'dist': current_dist + edge_data['length'], 'direction': 'backward'})

        # print(f"Ego graph created with {len(ego_graph.nodes)} nodes and {len(ego_graph.edges)} edges.")
        # Copy the CRS from the original graph to the ego_graph
        # ego_graph.graph['crs'] = local_map_graph.graph.get('crs', 'epsg:4326')
        # ox.plot_graph(ego_graph)
        return ego_graph

    def closest_point_on_line(self, A, B, P):
        # A and B are the endpoints of the line segment
        # P is the point for which we want to find the closest point on the line segment AB
        # Convert points to numpy arrays
        A = np.array(A)
        B = np.array(B)
        P = np.array(P)

        # Vector AB and AP
        AB = B - A
        AP = P - A

        # Projection of AP onto AB
        t = np.dot(AP, AB) / np.dot(AB, AB)

        # Clamp t to the range [0, 1] if you want the closest point on the segment
        t = max(0, min(1, t))

        # Closest point on the line
        closest_point = A + t * AB
        return closest_point


    def plot_map(self):
        # Set Zoom level and center
        zoom = 10
        center_lat = sum([lat for lat, lon in self.latlong]) / len(self.latlong)
        center_lon = sum([lon for lat, lon in self.latlong]) / len(self.latlong)

        # Initialize "data" attribute for plotly figure
        data1 = go.Scattermap(
            lat=[lat for lat, lon in self.latlong],
            lon=[lon for lat, lon in self.latlong],
            mode='lines+markers',
            marker=dict(size=5, color='blue'),
            line=dict(width=2, color='blue'),
            name='Route',
        )
        data2 = go.Scattermap(
            lat=[self.latlong[0][0]],
            lon=[self.latlong[0][1]],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='Current Position',
        )

        # Initialize "layout" attribute for plotly figure
        layout = go.Layout(
            title="Map during the drive",
            map=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom,
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
                ),
            ],
            sliders=[
                dict(
                    active=0,
                    currentvalue=dict(prefix='Time: ', visible=True, xanchor='right'),
                    steps=[]
                )
            ]
        )

        # Initialize slider steps
        steps = []
        for i in range(len(self.latlong)):
            current_position = {'lat': [[self.latlong[i][0]]], 'lon': [[self.latlong[i][1]]]}
            step = dict(
                label=f"{self.time[i]}",
                method='restyle',
                args=[current_position
                      , [1]] # Update the second trace
            )
            steps.append(step)
        layout['sliders'][0]['steps'] = steps

        # Create the map figure
        fig = go.Figure(data=[data1, data2], layout=layout)
        fig.show()