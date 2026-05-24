"""
Tìm K tuyến đường khác nhau giữa 2 điểm (Yen's k-shortest paths đơn giản hóa).
Dùng khi user muốn "gợi ý tuyến thay thế khi 1 cạnh bị chặn".
"""
from algorithms.dijkstra import dijkstra


def k_alternative_routes(G, source, target, weight_fn, k=3):
    """
    Trả về tối đa k tuyến khác nhau, mỗi lần chặn 1 cạnh khác trên tuyến gốc
    rồi chạy lại Dijkstra. Đây là biến thể đơn giản của Yen's algorithm.
    """
    base = dijkstra(G, source, target, weight_fn)
    if not base["found"]:
        return []

    results = [base]
    base_path = base["path"]

    # Thử chặn từng cạnh trên đường gốc; chọn k-1 tuyến mới khác biệt nhất
    candidates = []
    for i in range(len(base_path) - 1):
        blocked = {(base_path[i], base_path[i + 1])}
        alt = dijkstra(G, source, target, weight_fn, blocked_edges=blocked)
        if alt["found"] and alt["path"] != base_path:
            candidates.append(alt)

    # Loại trùng path (dedupe theo tuple)
    seen = {tuple(base_path)}
    for c in sorted(candidates, key=lambda x: x["cost"]):
        t = tuple(c["path"])
        if t not in seen:
            seen.add(t)
            results.append(c)
            if len(results) >= k:
                break
    return results
