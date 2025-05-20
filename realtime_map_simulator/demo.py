from realtime_map_simulator import MapEngine

map_engine = MapEngine()
map_engine.set_gnss_data('../drive_simulator/demo_virtual_drive.csv')
map_engine.plot_map()