import osmnx as ox
import matplotlib.pyplot as plt
import plotly.graph_objects as go
# ox.settings.log_console = True # Uncomment to enable logging to console

class BoundingBox:
    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

class MapAnalyzer:
    def __init__(self):
        self.bbox = None
        self.graph = None
        self.simplified_road_categories = {
            'highway': {
                'types': ['motorway', 'motorway_link'],
                'color': 'green'
            },
            'main_road': {
                'types': ['trunk', 'trunk_link', 'primary', 'primary_link'],
                'color': 'orange'
            },
            'secondary_road': {
                'types': ['secondary', 'secondary_link', 'tertiary', 'tertiary_link'],
                'color': 'blue'
            },
            'local_road': {
                'types': ['residential', 'living_street'],
                'color': 'gray'
            },
            'other': {
                'types': None,
                'color': 'lightgray'
            }
        }

    def add_bounding_box(self, bbox):
        if not isinstance(bbox, BoundingBox):
            raise ValueError("bbox must be an instance of BoundingBox class.")
        self.bbox = bbox

    def fetch_road_data(self):
        if self.bbox is None:
            raise ValueError("Bounding box is not set. Please set a bounding box using the 'add_bounding_box' method before fetching road data.")

        self.graph = ox.graph.graph_from_bbox(
            [self.bbox.left, self.bbox.bottom, self.bbox.right, self.bbox.top],
            network_type='drive',
            simplify=False,
            retain_all=True,
            # custom_filter='["highway"~"motorway|motorway_link"]'
        )
        # self.graph = ox.bearing.add_edge_bearings(self.graph)
        # self.graph = ox.distance.add_edge_lengths(self.graph)
        # self.graph = ox.routing.add_edge_speeds(self.graph)
        # self.graph = ox.routing.add_edge_travel_times(self.graph)

        # self.graph = ox.elevation.add_node_elevations_google(self.graph)
        # self.graph = ox.elevation.add_edge_grades(self.graph)

    def export_for_qgis(self, filepath='road_data.gpkg'):
        if self.graph is None:
            raise ValueError("No graph data available. Please fetch road data first using the 'fetch_road_data' method.")

        # Save data as geopackage to visualize in QGIS
        ox.save_graph_geopackage(self.graph, filepath=filepath, directed=True, encoding='utf-8')

    def show_road_stats(self):
        if self.graph is None:
            raise ValueError("No graph data available. Please fetch road data first using the 'fetch_road_data' method.")

        # Print basic statistics of the graph
        print("\nGraph Statistics:")
        print(f"  Nodes: {self.graph.number_of_nodes()}")
        print(f"  Edges: {self.graph.number_of_edges()}")

        # Display details of the first node and edge
        first_node = next(iter(self.graph.nodes(data=True)))
        print(f"\nFirst Node:\n  ID: {first_node[0]}\n  Attributes: {first_node[1]}")

        first_edge = next(iter(self.graph.edges(data=True)))
        print(f"\nFirst Edge:\n  From: {first_edge[0]}\n  To: {first_edge[1]}\n  Attributes: {first_edge[2]}")

        # Print the number of edges for each highway type
        # Ref: https://wiki.openstreetmap.org/wiki/Map_features#Highway
        print("\nNumber of edges based on OpenStreetMap highway type:")
        highway_types = set(edge_data.get('highway') for _, _, _, edge_data in self.graph.edges(keys=True, data=True))
        for highway_type in highway_types:
            if highway_type is None:
                continue
            count = sum(1 for _, _, _, edge_data in self.graph.edges(keys=True, data=True) if edge_data.get('highway') == highway_type)
            print(f"  {highway_type}: {count}")

    def simplify_road_classification(self):
        if self.graph is None:
            raise ValueError("No graph data available. Please fetch road data first using the 'fetch_road_data' method.")

        # Add category and color to each edge
        for u, v, k, edge_data in self.graph.edges(keys=True, data=True):
            highway_type = edge_data.get('highway', None)
            for category, attributes in self.simplified_road_categories.items():
                if attributes['types'] is None or highway_type in attributes['types']:
                    edge_data['simplified_highway_category'] = category
                    edge_data['simplified_highway_color'] = attributes['color']
                    break
            else:
                edge_data['simplified_highway_category'] = 'other'
                edge_data['simplified_highway_color'] = self.simplified_road_categories['other']['color']

        # Count edges for each category
        road_categories_count = {category: 0 for category in self.simplified_road_categories}
        for _, _, k, edge_data in self.graph.edges(keys=True, data=True):
            category = edge_data.get('simplified_highway_category', 'other')
            road_categories_count[category] += 1

        # Print edge count for each category
        print("\nNumber of edges based on simplified categories:")
        for category, count in road_categories_count.items():
            types = self.simplified_road_categories[category]['types']
            types_str = ', '.join(types) if types else 'All other types'
            print(f"  {category} ({types_str}): {count}")

    def plot_static_map(self):
        if self.graph is None:
            raise ValueError("No graph data available. Please fetch road data first using the 'fetch_road_data' method.")

        # Assign colors to edges based on highway type
        edges_color_list = []
        for u, v, k, edge_data in self.graph.edges(keys=True, data=True):
            color = edge_data.get('simplified_highway_color', 'lightgray')
            edges_color_list.append(color)

        # Plot the graph
        fig, ax = ox.plot_graph(self.graph, edge_color=edges_color_list, bgcolor='white', node_size=0)
        plt.show()

    def plot_interactive_map(self):
        if self.graph is None:
            raise ValueError("No graph data available. Please fetch road data first using the 'fetch_road_data' method.")

        # Set Zoom level and center
        zoom = 12
        center_lat = (self.bbox.top + self.bbox.bottom) / 2
        center_lon = (self.bbox.left + self.bbox.right) / 2

        # Create a background map
        fig = go.Figure()
        fig.update_layout(title="Roads classified for ADAS applications",
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
                            )
                          ]
                        )

        # Plot bounding box
        fig.add_scattermap(lat=[self.bbox.top, self.bbox.bottom, self.bbox.bottom, self.bbox.top, self.bbox.top],
                          lon=[self.bbox.left, self.bbox.left, self.bbox.right, self.bbox.right, self.bbox.left],
                          mode='lines',
                          line=dict(color='red', width=2),
                          name='Bounding Box'
                        )

        # convert graph to node and edge GeoPandas GeoDataFrames
        gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(self.graph)

        # Collect lines segments for each highway type
        plot_data = {}
        for _, edge in gdf_edges.iterrows():
            hwy_type = edge['simplified_highway_category']
            if hwy_type not in plot_data:
                plot_data[hwy_type] = {
                    'lat': [],
                    'lon': [],
                    'color': edge['simplified_highway_color']
                }
            plot_data[hwy_type]['lat'].extend(edge.geometry.xy[1])
            plot_data[hwy_type]['lat'].append(None)  # Add None to separate segments
            plot_data[hwy_type]['lon'].extend(edge.geometry.xy[0])
            plot_data[hwy_type]['lon'].append(None)  # Add None to separate segments

        # Plot the lines for each highway type
        for hwy_type, data in plot_data.items():
            line_width = 4 if hwy_type in ['highway', 'main_road'] else 1
            fig.add_scattermap(
                lat=data['lat'],
                lon=data['lon'],
                mode='lines',
                line=dict(color=data['color'], width=line_width),
                name=hwy_type
            )
        fig.show(renderer="browser")