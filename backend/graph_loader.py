"""
Tải và cache graph đường bộ Hà Nội từ OpenStreetMap qua osmnx.
Lần đầu chạy sẽ mất 1-3 phút để tải, các lần sau load từ file cache.
"""
import os
import pickle
import osmnx as ox
import networkx as nx
from math import radians, sin, cos, sqrt, atan2

CACHE_PATH = os.path.join(os.path.dirname(__file__), "hanoi_graph.pkl")
PLACE = "Hà Nội, Việt Nam"


def haversine(lat1, lon1, lat2, lon2):
    """Khoảng cách đường chim bay (mét) — dùng làm heuristic cho A*."""
    R = 6371000  # Bán kính Trái Đất (m)
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlam / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def load_graph():
    """Trả về (G, nodes_dict) — G là NetworkX MultiDiGraph, nodes_dict {id: (lat, lon)}."""
    if os.path.exists(CACHE_PATH):
        print(f"[graph] Load cache từ {CACHE_PATH}")
        with open(CACHE_PATH, "rb") as f:
            G = pickle.load(f)
    else:
        print(f"[graph] Tải graph Hà Nội từ OSM (mất ~1-3 phút lần đầu)...")
        G = ox.graph_from_place(PLACE, network_type="drive", simplify=True)
        # Thêm trường 'travel_time' (giây) dựa trên speed limit OSM
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        with open(CACHE_PATH, "wb") as f:
            pickle.dump(G, f)
        print(f"[graph] Đã cache {CACHE_PATH}")

    nodes_dict = {n: (data["y"], data["x"]) for n, data in G.nodes(data=True)}
    print(f"[graph] {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G, nodes_dict


def nearest_node(G, lat, lon):
    """Tìm node gần nhất với toạ độ (lat, lon)."""
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)
