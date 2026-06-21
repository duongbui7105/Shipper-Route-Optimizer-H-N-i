"""
Find K different routes between two nodes.

This is a compact Yen-style implementation that still uses the local
Dijkstra implementation.
"""
from algorithms.dijkstra import dijkstra


def _path_cost(G, path, weight_fn):
    total = 0.0
    for u, v in zip(path, path[1:]):
        edge_dict = G[u][v]
        total += min(weight_fn(u, v, ed) for ed in edge_dict.values())
    return total


def k_alternative_routes(G, source, target, weight_fn, k=3, blocked_edges=None):
    blocked_edges = set(blocked_edges or set())
    base = dijkstra(G, source, target, weight_fn, blocked_edges=blocked_edges)
    if not base["found"]:
        return []

    results = [base]
    candidates = []
    seen_candidates = set()

    for route_index in range(1, max(1, k)):
        previous_path = results[route_index - 1]["path"]

        for spur_index in range(len(previous_path) - 1):
            spur_node = previous_path[spur_index]
            root_path = previous_path[:spur_index + 1]
            root_key = tuple(root_path)

            spur_blocked_edges = set(blocked_edges)
            for route in results:
                route_path = route["path"]
                if len(route_path) > spur_index and tuple(route_path[:spur_index + 1]) == root_key:
                    spur_blocked_edges.add((route_path[spur_index], route_path[spur_index + 1]))

            spur = dijkstra(
                G,
                spur_node,
                target,
                weight_fn,
                blocked_edges=spur_blocked_edges,
                blocked_nodes=set(root_path[:-1]),
            )
            if not spur["found"]:
                continue

            total_path = root_path[:-1] + spur["path"]
            path_key = tuple(total_path)
            if path_key in seen_candidates or any(tuple(r["path"]) == path_key for r in results):
                continue

            seen_candidates.add(path_key)
            candidates.append({
                "path": total_path,
                "cost": _path_cost(G, total_path, weight_fn),
                "visited": spur["visited"],
                "runtime_ms": spur["runtime_ms"],
                "found": True,
            })

        if not candidates:
            break

        candidates.sort(key=lambda x: x["cost"])
        results.append(candidates.pop(0))

    return results[:k]
