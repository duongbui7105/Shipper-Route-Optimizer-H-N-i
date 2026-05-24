"""
A* search với heuristic = khoảng cách haversine tới đích.
So với Dijkstra: A* mở rộng ít node hơn nhờ heuristic admissible.
"""
import heapq
import time
from typing import Callable, Optional
from graph_loader import haversine


def astar(G, source, target, nodes_dict, weight_fn: Callable,
          heuristic_scale: float = 1.0, blocked_edges: Optional[set] = None):
    """
    nodes_dict: {node_id: (lat, lon)}
    heuristic_scale: nhân heuristic với hệ số quy đổi (vd: nếu weight là 'travel_time'
                     thì nhân 1/max_speed để đổi mét -> giây).
    """
    blocked_edges = blocked_edges or set()
    t0 = time.perf_counter()

    tlat, tlon = nodes_dict[target]

    def h(node):
        lat, lon = nodes_dict[node]
        return haversine(lat, lon, tlat, tlon) * heuristic_scale

    g_score = {source: 0.0}
    prev = {}
    visited = set()
    pq = [(h(source), 0.0, source)]
    pop_count = 0

    while pq:
        f, g, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        pop_count += 1

        if u == target:
            break

        for v, edge_dict in G[u].items():
            if (u, v) in blocked_edges:
                continue
            best_w = min(weight_fn(u, v, ed) for ed in edge_dict.values())
            ng = g + best_w
            if ng < g_score.get(v, float("inf")):
                g_score[v] = ng
                prev[v] = u
                heapq.heappush(pq, (ng + h(v), ng, v))

    runtime_ms = (time.perf_counter() - t0) * 1000

    if target not in g_score:
        return {"path": [], "cost": float("inf"), "visited": pop_count,
                "runtime_ms": runtime_ms, "found": False}

    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()

    return {
        "path": path,
        "cost": g_score[target],
        "visited": pop_count,
        "runtime_ms": runtime_ms,
        "found": True,
    }
