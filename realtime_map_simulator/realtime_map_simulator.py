import plotly.graph_objects as go
import pandas as pd

# Load the data
df = pd.read_csv('../drive_simulator/demo_virtual_drive.csv')

# Subsample the dataframe
time_delta_s  = df['timestamp_s'][1] - df['timestamp_s'][0]
if time_delta_s < 1:
    freq = int(1/time_delta_s)
    df = df.iloc[::freq].reset_index(drop=True)

# Extract latitude and longitude
latlong = df[['latitude_deg', 'longitude_deg']].values.tolist()
time = (df['timestamp_s'] - df['timestamp_s'].min()).round(1).values.tolist()

# Set Zoom level and center
zoom = 10
center_lat = sum([lat for lat, lon in latlong]) / len(latlong)
center_lon = sum([lon for lat, lon in latlong]) / len(latlong)

# Create the map figure
fig = go.Figure()
fig.update_layout(
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
)

# Plot the waypoints
fig.add_scattermap(
    lat=[lat for lat, lon in latlong],
    lon=[lon for lat, lon in latlong],
    mode='markers+lines',
    marker=dict(size=5, color='blue'),
    line=dict(width=2, color='blue'),
    name='Waypoints'
)

# Plot the slider
steps = []
for i in range(len(latlong)):
    steps.append(
        dict(
            label=str(time[i]),
            method='update',
            args=[
                {
                    'lat': [[latlong[i][0]]],
                    'lon': [[latlong[i][1]]],
                    'mode': 'markers+lines',
                    'marker': {'size': 10, 'color': 'red'},
                    'line': {'width': 4, 'color': 'red'},
                    'name': 'Current Position'
                }
            ]
        )
    )
fig.update_layout(
    sliders=[{
        'active': 0,
        'currentvalue': {'prefix': 'Time: ', 'visible': True, 'xanchor': 'right'},
        'steps': steps,
    }]
)

fig.show()