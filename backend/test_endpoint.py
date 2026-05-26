#!/usr/bin/env python
"""Test endpoint /route directly"""
import sys
import traceback
sys.path.insert(0, '.')

from main import app, STATE
from contextlib import asynccontextmanager
from graph_loader import load_graph, nearest_node
from traffic import TrafficSimulator, VEHICLE_PROFILES, make_weight_fn

# Manual initialization (simulating app startup)
print("=== Initializing STATE ===")
from graph_loader import load_graph
G, nodes_dict = load_graph()
STATE["G"] = G
STATE["nodes"] = nodes_dict
STATE["traffic"] = TrafficSimulator()
print(f"✓ STATE initialized")
print(f"  VEHICLE_PROFILES: {VEHICLE_PROFILES}")

# Now test the route function directly
print("\n=== Testing route function ===")
from pydantic import BaseModel
from typing import Optional

class Point(BaseModel):
    lat: float
    lon: float
    label: Optional[str] = None

class RouteReq(BaseModel):
    start: Point
    end: Point
    algorithm: str = "dijkstra"
    vehicle: str = "motorbike"
    mode: str = "time"

try:
    req = RouteReq(
        start=Point(lat=21.0285, lon=105.8542, label="Hồ Hoàn Kiếm"),
        end=Point(lat=21.0505, lon=105.8617, label="Tháp Rùa"),
        algorithm="dijkstra",
        vehicle="motorbike",
        mode="time"
    )
    print(f"Request: {req}")
    
    # Call the route function from main.py
    from main import route
    result = route(req)
    print(f"✓ Success!")
    print(f"  Distance: {result.get('distance_m')}")
    print(f"  Time: {result.get('time_s')}")
    print(f"  Coordinates: {len(result.get('coordinates', []))}")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
