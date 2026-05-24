"""
FastAPI app — REST endpoints cho frontend gọi.

Endpoints:
  POST /route               — tìm đường 1 điểm-tới-1 điểm
  POST /route/multi         — tối ưu nhiều điểm giao hàng (TSP)
  POST /route/compare       — so sánh Dijkstra vs A*
  POST /route/alternatives  — k tuyến thay thế
  POST /traffic/simulate    — bật/tắt mô phỏng kẹt xe
  GET  /history             — lịch sử
  DELETE /history           — xóa lịch sử
  GET  /vehicles            — danh sách phương tiện
  GET  /geocode?q=...       — tìm địa chỉ (proxy Nominatim)
"""
from contextlib import asynccontextmanager
from typing import List, Optional
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph_loader import load_graph, nearest_node
from traffic import TrafficSimulator, VEHICLE_PROFILES, make_weight_fn
from algorithms.dijkstra import dijkstra
from algorithms.astar import astar
from algorithms.tsp import solve_tsp
from algorithms.alternative import k_alternative_routes
import database

# State toàn cục — load 1 lần lúc khởi động
STATE = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== Khởi động backend ===")
    database.init_db()
    G, nodes_dict = load_graph()
    STATE["G"] = G
    STATE["nodes"] = nodes_dict
    STATE["traffic"] = TrafficSimulator()
    print("=== Sẵn sàng nhận request ===")
    yield


app = FastAPI(title="Shipper Route Optimizer — Hà Nội", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Models ----------
class Point(BaseModel):
    lat: float
    lon: float
    label: Optional[str] = None


class RouteReq(BaseModel):
    start: Point
    end: Point
    algorithm: str = Field("dijkstra", description="dijkstra | astar")
    vehicle: str = Field("motorbike", description="walking | motorbike | car")
    mode: str = Field("time", description="time | distance")


class MultiReq(BaseModel):
    start: Point
    waypoints: List[Point]
    return_to_start: bool = False
    vehicle: str = "motorbike"
    mode: str = "time"


class CompareReq(BaseModel):
    start: Point
    end: Point
    vehicle: str = "motorbike"
    mode: str = "time"


class AltReq(BaseModel):
    start: Point
    end: Point
    k: int = 3
    vehicle: str = "motorbike"
    mode: str = "time"


class TrafficReq(BaseModel):
    global_factor: float = 1.0
    random_fraction: float = 0.0  # 0..1, tỉ lệ cạnh bị kẹt ngẫu nhiên


# ---------- Helpers ----------
def _path_to_coords(path):
    return [STATE["nodes"][n] for n in path]


def _summarize(result, weight_fn, G):
    """Tính tổng quãng đường (m) và thời gian (s) cho 1 path."""
    path = result["path"]
    dist = 0.0
    time_s = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = min(G[u][v].values(), key=lambda d: d.get("length", float("inf")))
        dist += ed.get("length", 0.0)
        time_s += weight_fn(u, v, ed) if weight_fn else ed.get("travel_time", 0.0)
    return dist, time_s


def _make_segments(path, G):
    """Danh sách chặng đường có tên (cho 'list of segments')."""
    segs = []
    current_name = None
    current_dist = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = min(G[u][v].values(), key=lambda d: d.get("length", float("inf")))
        name = ed.get("name", "đường không tên")
        if isinstance(name, list):
            name = name[0]
        length = ed.get("length", 0.0)
        if name == current_name:
            current_dist += length
        else:
            if current_name is not None:
                segs.append({"name": current_name, "distance_m": round(current_dist, 1)})
            current_name = name
            current_dist = length
    if current_name is not None:
        segs.append({"name": current_name, "distance_m": round(current_dist, 1)})
    return segs


# ---------- Endpoints ----------
@app.get("/vehicles")
def get_vehicles():
    return VEHICLE_PROFILES


@app.get("/geocode")
def geocode(q: str):
    """Proxy Nominatim — giới hạn ở Hà Nội."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q + ", Hà Nội", "format": "json", "limit": 5,
                    "countrycodes": "vn"},
            headers={"User-Agent": "shipper-route-demo/1.0"},
            timeout=5,
        )
        return r.json()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/route")
def route(req: RouteReq):
    G = STATE["G"]; nodes = STATE["nodes"]; traffic = STATE["traffic"]
    s = nearest_node(G, req.start.lat, req.start.lon)
    t = nearest_node(G, req.end.lat, req.end.lon)
    wfn = make_weight_fn(traffic, req.mode, req.vehicle)

    if req.algorithm == "astar":
        scale = 1.0 / (max(p["speed_kmh"] for p in VEHICLE_PROFILES.values()) * 1000 / 3600) \
                if req.mode == "time" else 1.0
        result = astar(G, s, t, nodes, wfn, heuristic_scale=scale,
                       blocked_edges=traffic.blocked_edges)
    else:
        result = dijkstra(G, s, t, wfn, blocked_edges=traffic.blocked_edges)

    if not result["found"]:
        raise HTTPException(404, "Không tìm thấy đường đi")

    dist, time_s = _summarize(result, wfn, G)
    segs = _make_segments(result["path"], G)

    database.save({
        "start_label": req.start.label, "end_label": req.end.label,
        "waypoints": [], "algorithm": req.algorithm,
        "vehicle": req.vehicle, "mode": req.mode,
        "distance_m": dist, "time_s": time_s, "runtime_ms": result["runtime_ms"],
    })

    return {
        "coordinates": _path_to_coords(result["path"]),
        "distance_m": round(dist, 1),
        "time_s": round(time_s, 1),
        "segments": segs,
        "runtime_ms": round(result["runtime_ms"], 2),
        "visited_nodes": result["visited"],
        "algorithm": req.algorithm,
    }


@app.post("/route/multi")
def route_multi(req: MultiReq):
    """Tối ưu thứ tự ghé thăm nhiều điểm giao hàng (TSP)."""
    G = STATE["G"]; traffic = STATE["traffic"]
    pts = [req.start] + req.waypoints
    node_ids = [nearest_node(G, p.lat, p.lon) for p in pts]
    wfn = make_weight_fn(traffic, req.mode, req.vehicle)

    res = solve_tsp(G, node_ids, wfn, return_to_start=req.return_to_start)
    dist, time_s = _summarize({"path": res["full_path"]}, wfn, G)

    database.save({
        "start_label": req.start.label,
        "end_label": f"{len(req.waypoints)} điểm giao hàng",
        "waypoints": [w.model_dump() for w in req.waypoints],
        "algorithm": "TSP-" + res["method"],
        "vehicle": req.vehicle, "mode": req.mode,
        "distance_m": dist, "time_s": time_s, "runtime_ms": res["runtime_ms"],
    })

    return {
        "coordinates": _path_to_coords(res["full_path"]),
        "order": res["order"],   # index vào [start] + waypoints
        "legs": res["legs"],
        "distance_m": round(dist, 1),
        "time_s": round(time_s, 1),
        "runtime_ms": round(res["runtime_ms"], 2),
        "method": res["method"],
    }


@app.post("/route/compare")
def compare(req: CompareReq):
    """So sánh Dijkstra vs A* — cùng nguồn, cùng đích, cùng weight."""
    G = STATE["G"]; nodes = STATE["nodes"]; traffic = STATE["traffic"]
    s = nearest_node(G, req.start.lat, req.start.lon)
    t = nearest_node(G, req.end.lat, req.end.lon)
    wfn = make_weight_fn(traffic, req.mode, req.vehicle)

    d = dijkstra(G, s, t, wfn, blocked_edges=traffic.blocked_edges)
    scale = 1.0 / (max(p["speed_kmh"] for p in VEHICLE_PROFILES.values()) * 1000 / 3600) \
            if req.mode == "time" else 1.0
    a = astar(G, s, t, nodes, wfn, heuristic_scale=scale,
              blocked_edges=traffic.blocked_edges)

    if not d["found"] or not a["found"]:
        raise HTTPException(404, "Không tìm thấy đường đi")

    return {
        "dijkstra": {
            "coordinates": _path_to_coords(d["path"]),
            "cost": round(d["cost"], 2),
            "runtime_ms": round(d["runtime_ms"], 2),
            "visited_nodes": d["visited"],
        },
        "astar": {
            "coordinates": _path_to_coords(a["path"]),
            "cost": round(a["cost"], 2),
            "runtime_ms": round(a["runtime_ms"], 2),
            "visited_nodes": a["visited"],
        },
        "same_path": d["path"] == a["path"],
        "speedup": round(d["runtime_ms"] / a["runtime_ms"], 2) if a["runtime_ms"] > 0 else None,
    }


@app.post("/route/alternatives")
def alternatives(req: AltReq):
    """Trả về k tuyến thay thế khác nhau."""
    G = STATE["G"]; traffic = STATE["traffic"]
    s = nearest_node(G, req.start.lat, req.start.lon)
    t = nearest_node(G, req.end.lat, req.end.lon)
    wfn = make_weight_fn(traffic, req.mode, req.vehicle)

    results = k_alternative_routes(G, s, t, wfn, k=req.k)
    if not results:
        raise HTTPException(404, "Không tìm thấy đường đi")

    out = []
    for r in results:
        dist, time_s = _summarize(r, wfn, G)
        out.append({
            "coordinates": _path_to_coords(r["path"]),
            "distance_m": round(dist, 1),
            "time_s": round(time_s, 1),
            "cost": round(r["cost"], 2),
        })
    return {"routes": out}


@app.post("/traffic/simulate")
def traffic_sim(req: TrafficReq):
    t = STATE["traffic"]
    t.set_global(req.global_factor)
    if req.random_fraction > 0:
        t.random_congestion(STATE["G"], fraction=req.random_fraction)
    else:
        t.edge_factors.clear()
    return {
        "global_factor": t.global_factor,
        "congested_edges": len(t.edge_factors),
        "blocked_edges": len(t.blocked_edges),
    }


@app.post("/traffic/reset")
def traffic_reset():
    STATE["traffic"].unblock_all()
    STATE["traffic"].set_global(1.0)
    return {"ok": True}


@app.get("/history")
def history(limit: int = 20):
    return database.list_recent(limit)


@app.delete("/history")
def history_clear():
    database.clear_all()
    return {"ok": True}


@app.get("/")
def root():
    return {
        "name": "Shipper Route Optimizer — Hà Nội",
        "nodes": len(STATE["G"].nodes) if "G" in STATE else 0,
        "edges": len(STATE["G"].edges) if "G" in STATE else 0,
    }
