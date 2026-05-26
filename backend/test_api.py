#!/usr/bin/env python
"""Test script để debug API"""
import traceback
import sys
sys.path.insert(0, '.')

from graph_loader import load_graph, nearest_node
from traffic import VEHICLE_PROFILES, make_weight_fn, TrafficSimulator
from algorithms.dijkstra import dijkstra

try:
    print("=== Test 1: Load graph ===")
    G, nodes_dict = load_graph()
    print(f"✓ Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    print("\n=== Test 2: Find nearest nodes ===")
    s = nearest_node(G, 21.0285, 105.8542)
    t = nearest_node(G, 21.0505, 105.8617)
    print(f"✓ Source: {s}, Target: {t}")
    
    print(f"\n=== Test 3: Check VEHICLE_PROFILES ===")
    print(f"Available vehicles: {list(VEHICLE_PROFILES.keys())}")
    
    print(f"\n=== Test 4: Create weight function ===")
    traffic = TrafficSimulator()
    wfn = make_weight_fn(traffic, "time", "motorbike")
    print(f"✓ Weight function created")
    
    print(f"\n=== Test 5: Run dijkstra ===")
    result = dijkstra(G, s, t, wfn)
    print(f"✓ Dijkstra result: found={result['found']}, path_len={len(result['path'])}, cost={result['cost']}")
    
    if result['found']:
        print(f"  Path first 5 nodes: {result['path'][:5]}")
        
        print(f"\n=== Test 6: Convert path to coordinates ===")
        coords = [nodes_dict[n] for n in result['path']]
        print(f"✓ Coordinates: {len(coords)} points")
        print(f"  First 3: {coords[:3]}")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    traceback.print_exc()
