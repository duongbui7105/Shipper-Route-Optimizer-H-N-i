"""
Tải và cache graph đường bộ Hà Nội từ OpenStreetMap qua osmnx.
Lần đầu chạy sẽ mất 1-3 phút để tải, các lần sau load từ file cache.

Tối ưu: build BallTree trên edge midpoints để nearest_edge chạy O(log n)
thay vì duyệt toàn bộ edges.
"""
import os
import pickle
import numpy as np
import osmnx as ox
import networkx as nx
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point as ShPoint

CACHE_PATH = os.path.join(os.path.dirname(__file__), "hanoi_graph.pkl")
BTREE_PATH = os.path.join(os.path.dirname(__file__), "hanoi_edge_btree.pkl")
PLACE = "Hà Nội, Việt Nam"

# BallTree cache (eager-built khi load_graph() chạy)
_BTREE = None
_EDGE_INFO = None  # list of (u, v, key) aligned với BallTree.boxes


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
        print(f"[graph] Load cache from {CACHE_PATH}")
        with open(CACHE_PATH, "rb") as f:
            G = pickle.load(f)
    else:
        print("[graph] Download graph from OSM (first run can take ~1-3 minutes)...")
        G = ox.graph_from_place(PLACE, network_type="drive", simplify=True)
        # Thêm trường 'travel_time' (giây) dựa trên speed limit OSM
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        with open(CACHE_PATH, "wb") as f:
            pickle.dump(G, f)
        print(f"[graph] Cached {CACHE_PATH}")

    nodes_dict = {n: (data["y"], data["x"]) for n, data in G.nodes(data=True)}
    print(f"[graph] {len(G.nodes)} nodes, {len(G.edges)} edges")

    # Eager-build BallTree để click đầu tiên không phải đợi build
    _ensure_index(G)

    return G, nodes_dict


def nearest_node(G, lat, lon):
    """Tìm node gần nhất với toạ độ (lat, lon)."""
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)


def _build_edge_index(G):
    """Build BallTree trên edge midpoints (radians) — dùng haversine metric."""
    from sklearn.neighbors import BallTree
    pts = []
    info = []
    for u, v, k, data in G.edges(keys=True, data=True):
        if "geometry" in data:
            mid = data["geometry"].interpolate(0.5, normalized=True)
            lon, lat = mid.x, mid.y
        else:
            n1, n2 = G.nodes[u], G.nodes[v]
            lon = (n1["x"] + n2["x"]) / 2
            lat = (n1["y"] + n2["y"]) / 2
        pts.append([radians(lon), radians(lat)])
        info.append((int(u), int(v), int(k)))
    pts_rad = np.asarray(pts, dtype=np.float64)
    tree = BallTree(pts_rad, metric="haversine")
    return tree, info


def _ensure_index(G):
    """Load BallTree từ cache; build + save nếu chưa có."""
    global _BTREE, _EDGE_INFO
    if _BTREE is not None:
        return
    if os.path.exists(BTREE_PATH):
        try:
            with open(BTREE_PATH, "rb") as f:
                _BTREE, _EDGE_INFO = pickle.load(f)
            print(f"[graph] Loaded edge BallTree ({len(_EDGE_INFO)} edges) from cache")
            return
        except Exception as e:
            print(f"[graph] Failed to load BallTree cache ({e}), rebuilding...")
    print("[graph] Building edge BallTree (first run, ~5-15s)...")
    _BTREE, _EDGE_INFO = _build_edge_index(G)
    try:
        with open(BTREE_PATH, "wb") as f:
            pickle.dump((_BTREE, _EDGE_INFO), f)
        print(f"[graph] Cached {BTREE_PATH} ({len(_EDGE_INFO)} edges)")
    except Exception as e:
        print(f"[graph] Warning: could not cache BallTree ({e})")


def nearest_edge(G, lat, lon):
    """Tìm edge gần nhất với toạ độ (lat, lon). Trả về (u, v, key, dist_m).

    Dùng BallTree cached để lấy top-K candidates (O(log n)),
    rồi refine bằng geometry projection. Nhanh hơn nhiều so với osmnx mặc định.
    """
    _ensure_index(G)
    query_rad = np.array([[radians(lon), radians(lat)]], dtype=np.float64)
    K = 5  # top-K candidates từ BallTree
    dists, idxs = _BTREE.query(query_rad, k=K)
    best_u, best_v, best_key, best_d = None, None, None, float("inf")
    for idx in idxs[0]:
        u, v, key = _EDGE_INFO[idx]
        ed = G[u][v][key]
        if "geometry" in ed:
            # Fast path: khoảng cách tới các coords của edge
            coords = list(ed["geometry"].coords)
            d = min(haversine(lat, lon, y, x) for x, y in coords)
            if d < best_d:
                best_u, best_v, best_key, best_d = u, v, key, d
            # Refine: project point onto geometry
            try:
                point = ShPoint(lon, lat)
                proj = ed["geometry"].interpolate(ed["geometry"].project(point))
                d = haversine(lat, lon, proj.y, proj.x)
                if d < best_d:
                    best_u, best_v, best_key, best_d = u, v, key, d
            except Exception:
                pass
        else:
            n1, n2 = G.nodes[u], G.nodes[v]
            d = min(
                haversine(lat, lon, n1["y"], n1["x"]),
                haversine(lat, lon, n2["y"], n2["x"]),
            )
            if d < best_d:
                best_u, best_v, best_key, best_d = int(u), int(v), int(key), d
    return best_u, best_v, best_key, best_d
