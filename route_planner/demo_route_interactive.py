from route_planner import RoutePlanner, Waypoint

waypoints = [
    Waypoint(37.6130184, -122.39625356),  # near SF airport
    Waypoint(37.4213068, -122.093090),    # near Google
    Waypoint(37.365739, -121.905370)      # near SJ airport
]
route_planner = RoutePlanner()
route_planner.add_waypoints(waypoints)
route_planner.calculate_route()
# route_planner.calculateVirtualDrive(speed, freq)
route_planner.plot_interactive_map()