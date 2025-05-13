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

# Initialize "data" attribute for plotly figure
data1 = go.Scattermap(
    lat=[lat for lat, lon in latlong],
    lon=[lon for lat, lon in latlong],
    mode='lines+markers',
    marker=dict(size=5, color='blue'),
    line=dict(width=2, color='blue'),
    name='Route',
)
data2 = go.Scattermap(
    lat=[latlong[0][0]],
    lon=[latlong[0][1]],
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
for i in range(len(latlong)):
    current_position = {'lat': [[latlong[i][0]]], 'lon': [[latlong[i][1]]]}
    step = dict(
        label=f"{time[i]}",
        method='restyle',
        args=[current_position, [1]] # Update the second trace
    )
    steps.append(step)
layout['sliders'][0]['steps'] = steps

# Create the map figure
fig = go.Figure(data=[data1, data2], layout=layout)
fig.show()