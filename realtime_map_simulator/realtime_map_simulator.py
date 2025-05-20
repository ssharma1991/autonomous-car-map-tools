import plotly.graph_objects as go
import pandas as pd

class MapEngine:
    def __init__(self):
        self.latlong = []
        self.time = []

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

    def calculate_realtime_map(self):
        # This function is a placeholder for any real-time map calculations
        # Currently, it does not perform any operations
        pass

    def get_map_at_latlong(self, latlong):
        # This function is a placeholder for getting map data at a specific latitude and longitude
        # Currently, it does not perform any operations
        pass

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