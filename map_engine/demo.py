#!/usr/bin/env python3

from realtime_map_simulator import MapEngine

map_engine = MapEngine()
map_engine.set_gnss_data('../drive_simulator/demo_virtual_drive.csv')
map_engine.calculate_realtime_map()
map_engine.plot_map()