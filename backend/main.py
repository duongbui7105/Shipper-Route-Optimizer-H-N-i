"""
FastAPI app — REST endpoints cho frontend gọi.

Endpoints:
  POST /route               — tìm đường 1 điểm-tới-1 điểm
  POST /route/multi         — tối ưu nhiều điểm giao hàng (TSP)
  POST /route/compare       — so sánh Dijkstra vs A*
  POST /graph/nearest_edge  — tìm cạnh gần nhất trên bản đồ
  POST /traffic/simulate    — bật/tắt mô phỏng kẹt xe
  GET  /history             — lịch sử
  DELETE /history           — xóa lịch sử
  GET  /vehicles            — danh sách phương tiện
  GET  /geocode?q=...       — tìm địa chỉ (proxy Nominatim)
"""
from contextlib import asynccontextmanager
from typing import List, Optional
import requests
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from graph_loader import load_graph, nearest_node, nearest_edge
from traffic import TrafficSimulator, VEHICLE_PROFILES, make_weight_fn
from algorithms.dijkstra import dijkstra
from algorithms.astar import astar
from algorithms.tsp import solve_tsp
import database

# State toàn cục — load 1 lần lúc khởi động
STATE = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== Backend starting ===")
    database.init_db()
    G, nodes_dict = load_graph()
    STATE["G"] = G
    STATE["nodes"] = nodes_dict
    STATE["traffic"] = TrafficSimulator()
    print("=== Backend ready ===")
    yield


app = FastAPI(title="Shipper Route Optimizer — Hà Nội", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"ERROR: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
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
    blocked_edges: List[List[int]] = Field(default_factory=list)


class MultiReq(BaseModel):
    start: Point
    waypoints: List[Point]
    return_to_start: bool = False
    vehicle: str = "motorbike"
    mode: str = "time"
    blocked_edges: List[List[int]] = Field(default_factory=list)


class CompareReq(BaseModel):
    start: Point
    end: Point
    vehicle: str = "motorbike"
    mode: str = "time"
    blocked_edges: List[List[int]] = Field(default_factory=list)


class NearestEdgeReq(BaseModel):
    lat: float
    lon: float


class TrafficReq(BaseModel):
    global_factor: float = 1.0
    random_fraction: float = 0.0  # 0..1, tỉ lệ cạnh bị kẹt ngẫu nhiên


# ---------- Helpers ----------
def _path_to_coords(path):
    return [STATE["nodes"][n] for n in path]


def _edge_to_coords(G, u, v, key):
    ed = G[u][v][key]
    if "geometry" in ed:
        return [(lat, lon) for lon, lat in ed["geometry"].coords]
    return _path_to_coords([u, v])


def _blocked_edges_from_req(req_edges, traffic):
    blocked = set(traffic.blocked_edges)
    for edge in req_edges or []:
        if len(edge) < 2:
            continue
        u, v = int(edge[0]), int(edge[1])
        blocked.add((u, v))
        blocked.add((v, u))
    return blocked


def _time_weight_fn(traffic, vehicle):
    speed_mps = VEHICLE_PROFILES[vehicle]["speed_kmh"] * 1000 / 3600

    def w(u, v, ed):
        length = ed.get("length", 1.0)
        return length / speed_mps * traffic.factor(u, v)

    return w


def _heuristic_scale(mode, traffic):
    min_factor = traffic.global_factor
    if mode == "time":
        max_speed_mps = max(p["speed_kmh"] for p in VEHICLE_PROFILES.values()) * 1000 / 3600
        return min_factor / max_speed_mps
    return min_factor


def _summarize(result, weight_fn, G, traffic, vehicle):
    """Tính tổng quãng đường (m) và thời gian (s) cho 1 path."""
    path = result["path"]
    dist = 0.0
    time_s = 0.0
    time_weight_fn = _time_weight_fn(traffic, vehicle)
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        ed = min(G[u][v].values(), key=lambda d: weight_fn(u, v, d))
        dist += ed.get("length", 0.0)
        time_s += time_weight_fn(u, v, ed)
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


@app.post("/graph/nearest_edge")
def graph_nearest_edge(req: NearestEdgeReq):
    G = STATE["G"]
    u, v, key, dist = nearest_edge(G, req.lat, req.lon)
    ed = G[u][v][key]
    name = ed.get("name", "Đường không tên")
    if isinstance(name, list):
        name = name[0]
    return {
        "u": u,
        "v": v,
        "key": key,
        "name": name,
        "length_m": round(ed.get("length", 0.0), 1),
        "distance_m": round(dist, 1),
        "coordinates": _edge_to_coords(G, u, v, key),
    }


@app.post("/route")
def route(req: RouteReq):
    try:
        G = STATE["G"]; nodes = STATE["nodes"]; traffic = STATE["traffic"]
        s = nearest_node(G, req.start.lat, req.start.lon)
        t = nearest_node(G, req.end.lat, req.end.lon)
        wfn = make_weight_fn(traffic, req.mode, req.vehicle)
        blocked_edges = _blocked_edges_from_req(req.blocked_edges, traffic)

        if req.algorithm == "astar":
            result = astar(G, s, t, nodes, wfn, heuristic_scale=_heuristic_scale(req.mode, traffic),
                           blocked_edges=blocked_edges)
        else:
            result = dijkstra(G, s, t, wfn, blocked_edges=blocked_edges)

        if not result["found"]:
            raise HTTPException(404, "Không tìm thấy đường đi")

        dist, time_s = _summarize(result, wfn, G, traffic, req.vehicle)
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"[route] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/route/multi")
def route_multi(req: MultiReq):
    """Tối ưu thứ tự ghé thăm nhiều điểm giao hàng (TSP)."""
    G = STATE["G"]; traffic = STATE["traffic"]
    pts = [req.start] + req.waypoints
    node_ids = [nearest_node(G, p.lat, p.lon) for p in pts]
    wfn = make_weight_fn(traffic, req.mode, req.vehicle)
    blocked_edges = _blocked_edges_from_req(req.blocked_edges, traffic)

    res = solve_tsp(G, node_ids, wfn, return_to_start=req.return_to_start, blocked_edges=blocked_edges)
    if not res["full_path"]:
        raise HTTPException(404, "Khong tim thay duong di")
    dist, time_s = _summarize({"path": res["full_path"]}, wfn, G, traffic, req.vehicle)

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
    blocked_edges = _blocked_edges_from_req(req.blocked_edges, traffic)

    d = dijkstra(G, s, t, wfn, blocked_edges=blocked_edges)
    a = astar(G, s, t, nodes, wfn, heuristic_scale=_heuristic_scale(req.mode, traffic),
              blocked_edges=blocked_edges)

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
