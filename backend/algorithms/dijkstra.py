"""
Cài đặt Dijkstra trên MultiDiGraph của NetworkX.
KHÔNG dùng nx.shortest_path — đây là implementation thủ công bằng min-heap.
"""
import heapq
import time
from typing import Callable, Optional


def dijkstra(G, source, target, weight_fn: Callable, blocked_edges: Optional[set] = None,
             blocked_nodes: Optional[set] = None):
    """
    Trả về dict {
      'path': [node_ids],
      'cost': tổng weight,
      'visited': số node đã pop,
      'runtime_ms': float
    }

    weight_fn(u, v, edge_data) -> float : hàm tính weight của một cạnh.
    blocked_edges: set các (u, v) bị chặn (mô phỏng tuyến đường bị tắc).
    """
    blocked_edges = blocked_edges or set()
    blocked_nodes = blocked_nodes or set()
    t0 = time.perf_counter()

    if source in blocked_nodes or target in blocked_nodes:
        return {"path": [], "cost": float("inf"), "visited": 0,
                "runtime_ms": 0.0, "found": False}

    dist = {source: 0.0}
    prev = {}
    visited = set()
    pq = [(0.0, source)]
    pop_count = 0

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        pop_count += 1

        if u == target:
            break

        # Duyệt các cạnh ra khỏi u. MultiDiGraph: có thể nhiều cạnh giữa 2 node.
        for v, edge_dict in G[u].items():
            if v in blocked_nodes:
                continue
            if (u, v) in blocked_edges:
                continue
            # Lấy cạnh có weight nhỏ nhất giữa u và v
            best_w = min(weight_fn(u, v, ed) for ed in edge_dict.values())
            nd = d + best_w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    runtime_ms = (time.perf_counter() - t0) * 1000

    if target not in dist:
        return {"path": [], "cost": float("inf"), "visited": pop_count,
                "runtime_ms": runtime_ms, "found": False}

    # Truy ngược path
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()

    return {
        "path": path,
        "cost": dist[target],
        "visited": pop_count,
        "runtime_ms": runtime_ms,
        "found": True,
    }
