"""
Bài toán shipper: từ điểm xuất phát, ghé qua N điểm giao hàng theo thứ tự tối ưu,
(tùy chọn) quay về điểm xuất phát.

Cách tiếp cận:
1. Tính ma trận khoảng cách giữa mọi cặp điểm bằng Dijkstra
2. Nearest Neighbor → lời giải khởi tạo
3. 2-opt → cải thiện cục bộ
4. N <= 9: thêm bước brute-force (đảm bảo tối ưu) nếu thời gian cho phép
"""
import time
from itertools import permutations
from algorithms.dijkstra import dijkstra


def build_distance_matrix(G, nodes, weight_fn, blocked_edges=None):
    """Trả về ma trận [N][N] cost và [N][N] path (list node_id)."""
    n = len(nodes)
    cost = [[0.0] * n for _ in range(n)]
    paths = [[[] for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            r = dijkstra(G, nodes[i], nodes[j], weight_fn, blocked_edges=blocked_edges)
            cost[i][j] = r["cost"]
            paths[i][j] = r["path"]
    return cost, paths


def nearest_neighbor(cost, start_idx=0):
    n = len(cost)
    visited = [False] * n
    visited[start_idx] = True
    tour = [start_idx]
    for _ in range(n - 1):
        u = tour[-1]
        best, best_d = -1, float("inf")
        for v in range(n):
            if not visited[v] and cost[u][v] < best_d:
                best_d, best = cost[u][v], v
        tour.append(best)
        visited[best] = True
    return tour


def tour_cost(tour, cost, return_to_start=False):
    total = sum(cost[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))
    if return_to_start:
        total += cost[tour[-1]][tour[0]]
    return total


def two_opt(tour, cost, return_to_start=False, max_iter=200):
    """Cải thiện tour bằng cách đảo các đoạn (2-opt swap)."""
    best = tour[:]
    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        it += 1
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                # Đảo ngược đoạn [i..j]
                new = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if tour_cost(new, cost, return_to_start) < tour_cost(best, cost, return_to_start):
                    best = new
                    improved = True
    return best


def solve_tsp(G, point_nodes, weight_fn, return_to_start=False, brute_force_limit=8, blocked_edges=None):
    """
    point_nodes[0] = điểm xuất phát; point_nodes[1..] = các điểm giao hàng.
    Trả về thứ tự ghé thăm tối ưu (indices vào point_nodes), tổng cost, và
    các path Dijkstra nối các chặng.
    """
    t0 = time.perf_counter()
    n = len(point_nodes)
    cost, paths = build_distance_matrix(G, point_nodes, weight_fn, blocked_edges=blocked_edges)
    for i in range(n):
        for j in range(n):
            if i != j and not paths[i][j]:
                return {
                    "order": [],
                    "total_cost": float("inf"),
                    "legs": [],
                    "full_path": [],
                    "method": "unreachable",
                    "runtime_ms": (time.perf_counter() - t0) * 1000,
                }

    if n <= brute_force_limit:
        # Brute force: cố định start, thử mọi hoán vị các điểm còn lại
        best_tour = None
        best_c = float("inf")
        for perm in permutations(range(1, n)):
            tour = [0] + list(perm)
            c = tour_cost(tour, cost, return_to_start)
            if c < best_c:
                best_c, best_tour = c, tour
        tour = best_tour
        method = "brute_force"
    else:
        init = nearest_neighbor(cost, 0)
        tour = two_opt(init, cost, return_to_start)
        method = "nearest_neighbor + 2-opt"

    total_cost = tour_cost(tour, cost, return_to_start)

    # Ghép các chặng thành 1 path liền
    full_path = []
    legs = []
    seq = tour + ([tour[0]] if return_to_start else [])
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        leg_path = paths[a][b]
        legs.append({"from_idx": a, "to_idx": b, "cost": cost[a][b]})
        if i == 0:
            full_path.extend(leg_path)
        else:
            full_path.extend(leg_path[1:])  # tránh trùng node nối

    return {
        "order": tour,
        "total_cost": total_cost,
        "legs": legs,
        "full_path": full_path,
        "method": method,
        "runtime_ms": (time.perf_counter() - t0) * 1000,
    }
