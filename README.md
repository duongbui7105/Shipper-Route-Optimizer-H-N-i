# 🛵 Shipper Route Optimizer — Hà Nội

Ứng dụng web tìm lộ trình tối ưu cho shipper trên bản đồ Hà Nội thật, có cài đặt thủ công các thuật toán đồ thị (Dijkstra, A*, TSP).

## ✨ Tính năng

### Bắt buộc
- ✅ Bản đồ tương tác (Leaflet + OpenStreetMap)
- ✅ Chọn điểm xuất phát/đến bằng **click** hoặc **tìm địa chỉ** (Nominatim)
- ✅ Tính & vẽ tuyến đường tối ưu trên bản đồ
- ✅ Hiển thị tổng quãng đường, thời gian, danh sách chặng đường (có tên đường)
- ✅ **Thuật toán tự cài đặt trên graph thật** (Dijkstra + A*, không gọi `nx.shortest_path`)
- ✅ Lưu lịch sử tìm đường (SQLite)

### Nâng cao
- ✅ **Tối ưu nhiều điểm giao hàng** — bài toán TSP (brute-force ≤8 điểm, nearest neighbor + 2-opt cho nhiều điểm hơn)
- ✅ **So sánh Dijkstra vs A*** theo runtime và số node đã duyệt
- ✅ **3 loại phương tiện**: đi bộ, xe máy, ô tô (tốc độ trung bình Hà Nội)
- ✅ **Mô phỏng kẹt xe** bằng trọng số động (global factor + random per-edge)
- ✅ **Tuyến thay thế** khi 1 cạnh bị chặn (Yen's k-shortest paths đơn giản hóa)

### Yêu cầu phi chức năng
- ✅ **Kiến trúc tách lớp**: `frontend/src/api/` (data) ↔ `components/` (UI) ↔ `backend/algorithms/` (logic)
- ✅ Lưu trữ: SQLite local
- ✅ Demo: dữ liệu mẫu sẵn (xem mục Kịch bản demo)

---

## 🚀 Cài đặt & chạy

### Yêu cầu
- Python 3.10+
- Node.js 18+
- Khoảng 500 MB dung lượng cho graph cache Hà Nội

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> ⏳ **Lần đầu chạy** mất 1–3 phút để tải graph Hà Nội từ OSM (~200k node).
> Sau đó cache vào `hanoi_graph.pkl`, các lần sau khởi động chỉ ~5 giây.

Sau khi backend sẵn sàng sẽ in:
```
[graph] 198432 nodes, 461203 edges
=== Sẵn sàng nhận request ===
```

### Frontend (React + Vite)

Mở terminal mới:

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:5173

---

## 📂 Cấu trúc thư mục

```
shipper-route/
├── backend/
│   ├── main.py                  # FastAPI app + REST endpoints
│   ├── graph_loader.py          # Tải/cache graph từ OSM qua osmnx
│   ├── traffic.py               # Vehicle profiles + traffic simulator
│   ├── database.py              # SQLite cho lịch sử
│   ├── algorithms/              # 🎯 Thuật toán TỰ CÀI
│   │   ├── dijkstra.py          #   Dijkstra với min-heap
│   │   ├── astar.py             #   A* với heuristic haversine
│   │   ├── tsp.py               #   TSP (brute-force + nearest neighbor + 2-opt)
│   │   └── alternative.py       #   k-shortest paths
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx              # Composition root
    │   ├── api/client.js        # 🎯 Lớp DATA (tách khỏi UI)
    │   ├── components/          # 🎯 Lớp UI
    │   │   ├── MapView.jsx
    │   │   ├── ControlPanel.jsx
    │   │   ├── RouteInfo.jsx
    │   │   ├── HistoryPanel.jsx
    │   │   ├── ComparisonView.jsx
    │   │   └── SearchBox.jsx
    │   └── styles/app.css
    ├── package.json
    └── vite.config.js           # proxy /api → :8000
```

---

## 🎬 Kịch bản demo

### 1. Tìm đường cơ bản (Dijkstra tự cài)
1. Chọn tab **"1 điểm"**
2. Tìm "Hồ Hoàn Kiếm" → click kết quả
3. Tìm "Đại học Bách Khoa Hà Nội" → click kết quả
4. Bấm **"Tìm đường"**
5. Xem: ~3.5 km, ~9 phút (xe máy), danh sách đường: Đinh Tiên Hoàng → Lê Thái Tổ → ...

### 2. So sánh Dijkstra vs A*
1. Sang tab **"So sánh"**
2. Chọn 2 điểm xa nhau (vd: Mỹ Đình → Long Biên)
3. Bấm **"So sánh Dijkstra vs A*"**
4. Quan sát: A* duyệt ít node hơn ~3–5×, runtime nhanh hơn tương ứng

### 3. Shipper với 4 điểm giao hàng (TSP)
1. Sang tab **"Nhiều điểm"**
2. Click trên map: 1 điểm xuất phát (kho) + 4 điểm giao
3. Tick **"Quay về điểm xuất phát"**
4. Bấm **"Tối ưu"** → backend chạy brute-force tìm thứ tự tối ưu

### 4. Mô phỏng kẹt xe
1. Tìm đường thường, ghi nhớ thời gian
2. Kéo **"Hệ số chung"** lên 2.0 + **"Tỉ lệ kẹt"** 10%
3. Tìm lại cùng tuyến → thời gian tăng, có thể tuyến cũng đổi

### 5. Tuyến thay thế
1. Sang tab **"Tuyến thay thế"** → chọn 2 điểm → bấm tìm
2. 3 tuyến hiện đồng thời với màu khác nhau

---

## 🧠 Chi tiết thuật toán

### Dijkstra (`algorithms/dijkstra.py`)
- Min-heap (`heapq`) với key = tổng cost từ source
- Hỗ trợ `blocked_edges` để bỏ qua cạnh bị chặn
- Trả về: path, cost, số node đã pop (visited), runtime_ms

### A* (`algorithms/astar.py`)
- Heuristic: khoảng cách haversine (đường chim bay) tới đích — admissible & consistent
- Khi `mode=time`: nhân heuristic với `1/v_max` để đổi đơn vị (m → s)
- Cùng interface với Dijkstra để so sánh fair

### TSP (`algorithms/tsp.py`)
- N ≤ 8: brute force mọi hoán vị (đảm bảo tối ưu tuyệt đối)
- N > 8: nearest neighbor → 2-opt local search
- Khoảng cách giữa các điểm = Dijkstra trên graph thật

### k-shortest paths (`algorithms/alternative.py`)
- Biến thể đơn giản của Yen's: chặn từng cạnh trên tuyến gốc rồi re-run Dijkstra
- Dedupe + sort theo cost, trả về k tuyến rẻ nhất

---

## 🔌 API endpoints (Backend FastAPI — http://localhost:8000)

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Trạng thái server + kích thước graph |
| `/vehicles` | GET | Danh sách phương tiện |
| `/geocode?q=...` | GET | Tìm địa chỉ (Nominatim) |
| `/route` | POST | Tìm 1 tuyến |
| `/route/multi` | POST | TSP nhiều điểm |
| `/route/compare` | POST | So sánh Dijkstra vs A* |
| `/route/alternatives` | POST | k tuyến thay thế |
| `/traffic/simulate` | POST | Đặt mô phỏng kẹt xe |
| `/traffic/reset` | POST | Reset traffic |
| `/history` | GET / DELETE | Lịch sử |

Docs đầy đủ: http://localhost:8000/docs (FastAPI tự sinh).

---

## ⚠ Lưu ý

- **Geocode**: dùng Nominatim public — giới hạn 1 request/giây. Đừng spam.
- **Graph cache**: file `hanoi_graph.pkl` khoảng 100–200 MB. Đừng commit vào git.
- **Lần đầu chạy backend** rất chậm — chờ thấy log "Sẵn sàng nhận request" rồi mới gọi từ frontend.
- Nếu muốn thử khu vực khác, sửa biến `PLACE` trong `graph_loader.py` rồi xóa cache cũ.

## 📝 Báo cáo (gợi ý cho slide demo)

Khi báo cáo, có thể highlight:
1. **Thuật toán tự cài trên graph thật**: không gọi `nx.shortest_path` — dùng heap thủ công
2. **Kết quả so sánh A* vs Dijkstra**: chạy 10 cặp điểm random, lập bảng/chart
3. **TSP**: cho thấy thứ tự ghé thăm tối ưu khác hẳn thứ tự ngẫu nhiên
4. **Traffic simulation**: tăng global_factor → thời gian tăng tuyến tính; random edges → tuyến đường có thể đổi (graph thay đổi tô-pô weight)
5. **Tách lớp**: `api/client.js` không biết Leaflet, `MapView.jsx` không biết fetch, `algorithms/` không biết HTTP
