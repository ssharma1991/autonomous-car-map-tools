from drive_simulator import DriveSimulator, Waypoint

waypoints = [
    Waypoint(37.6130184, -122.39625356),  # near SF airport
    Waypoint(37.4213068, -122.093090),    # near Google
    Waypoint(37.365739, -121.905370)      # near SJ airport
]

# Initialize
drive_sim = DriveSimulator()
drive_sim.add_waypoints(waypoints)

# Calculate route and simulate virtual drive
drive_sim.calculate_route()
drive_sim.simulate_virtual_drive()
# drive_sim.simulate_virtual_drive(45, 10) # Manually set speed and distance
drive_sim.save_virtual_drive()
drive_sim.show_metrics()

# Visualize route and drive
drive_sim.plot_interactive_map()
drive_sim.plot_static_map() # Set zoom level automatically
# drive_sim.plot_static_map(12)  # Set zoom level manually


