"""
- Vehicle profiles: tốc độ trung bình cho từng phương tiện ở Hà Nội.
- Traffic simulation: nhân weight cạnh với hệ số mô phỏng kẹt xe.
"""
import random

# Tốc độ trung bình thực tế ở Hà Nội (km/h), đã tính tới điều kiện giao thông
VEHICLE_PROFILES = {
    "walking":    {"speed_kmh": 5, "label": "Đi bộ"},
    "motorbike":  {"speed_kmh": 28, "label": "Xe máy"},  # phổ biến cho shipper
    "car":        {"speed_kmh": 45, "label": "Ô tô"},
}


class TrafficSimulator:
    """
    Quản lý hệ số kẹt xe trên từng cạnh.
    - global_factor: hệ số chung (vd: 1.5 = chậm hơn 50%)
    - edge_factors: {(u,v): factor} — kẹt xe cục bộ trên 1 số tuyến
    - blocked_edges: set — cạnh bị chặn hoàn toàn
    """
    def __init__(self):
        self.global_factor = 1.0
        self.edge_factors = {}
        self.blocked_edges = set()

    def set_global(self, factor: float):
        self.global_factor = max(0.5, min(5.0, factor))

    def block_edge(self, u, v):
        self.blocked_edges.add((u, v))
        self.blocked_edges.add((v, u))

    def unblock_all(self):
        self.blocked_edges.clear()
        self.edge_factors.clear()

    def random_congestion(self, G, fraction: float = 0.1, max_factor: float = 3.0):
        """Tạo kẹt xe ngẫu nhiên trên `fraction` các cạnh."""
        self.edge_factors.clear()
        all_edges = list(G.edges(keys=True))
        k = int(len(all_edges) * fraction)
        for u, v, _key in random.sample(all_edges, k):
            self.edge_factors[(u, v)] = random.uniform(1.5, max_factor)

    def factor(self, u, v):
        return self.global_factor * self.edge_factors.get((u, v), 1.0)

    def weight(self, u, v, edge_data, base_attr="travel_time"):
        """Hàm dùng làm weight_fn cho Dijkstra/A*."""
        base = edge_data.get(base_attr)
        if base is None:
            # fallback: length / speed
            base = edge_data.get("length", 1.0) / 8.33  # 30 km/h default
        return base * self.factor(u, v)


def make_weight_fn(traffic: TrafficSimulator, mode: str, profile: str):
    """
    mode: 'distance' (tối ưu quãng đường, mét) hoặc 'time' (tối ưu thời gian, giây)
    profile: 'walking' | 'motorbike' | 'car'
    """
    if mode == "distance":
        def w(u, v, ed):
            return ed.get("length", 1.0) * traffic.factor(u, v)
        return w

    # mode == 'time'
    speed_mps = VEHICLE_PROFILES[profile]["speed_kmh"] * 1000 / 3600

    def w(u, v, ed):
        length = ed.get("length", 1.0)
        base_time = length / speed_mps  # giây
        return base_time * traffic.factor(u, v)
    return w
