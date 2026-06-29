import { useState } from 'react'
import MapView from './components/MapView'
import ControlPanel from './components/ControlPanel'
import RouteInfo from './components/RouteInfo'
import HistoryPanel from './components/HistoryPanel'
import ComparisonView from './components/ComparisonView'
import { api } from './api/client'

export default function App() {
  const [mode, setMode] = useState('single') // single | multi | compare | alt
  const [start, setStart] = useState(null)
  const [end, setEnd] = useState(null)
  const [waypoints, setWaypoints] = useState([])

  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [vehicle, setVehicle] = useState('motorbike')
  const [optMode, setOptMode] = useState('time')
  const [returnToStart, setReturnToStart] = useState(false)

  const [routes, setRoutes] = useState([])         // mảng hiển thị trên map
  const [routeInfo, setRouteInfo] = useState(null) // metadata kết quả chính
  const [compareData, setCompareData] = useState(null)
  const [blockMode, setBlockMode] = useState(false)
  const [blockedEdges, setBlockedEdges] = useState([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [historyKey, setHistoryKey] = useState(0)

  const refreshHistory = () => setHistoryKey((k) => k + 1)
  const blockedEdgePayload = () => blockedEdges.map((e) => [e.u, e.v, e.key])

  // Map click handler — quy tắc:
  // - single/compare/alt: click 1 đặt start, click 2 đặt end
  // - multi: click 1 đặt start, các click sau thêm waypoint
  const handleMapClick = async (latlng) => {
    if (mode === 'alt' && blockMode) {
      // Click chọn đường bị chặn — gọi API và hiển thị polyline khi có kết quả
      try {
        const edge = await api.nearestEdge(latlng.lat, latlng.lng)
        if (edge.distance_m > 1000) {
          setErr(`Click cách đường gần nhất ${edge.distance_m.toFixed(0)} m, vượt ngưỡng 1000 m`)
          return
        }
        setErr('')
        setBlockedEdges((items) => {
          if (items.some((e) => e.u === edge.u && e.v === edge.v && e.key === edge.key)) {
            return items
          }
          return [...items, edge]
        })
      } catch (e) {
        setErr(String(e.message || e))
      }
      return
    }
    const p = { lat: latlng.lat, lon: latlng.lng }
    if (!start) { setStart(p); return }
    if (mode === 'multi') {
      setWaypoints((w) => [...w, p])
    } else {
      setEnd(p)
    }
  }

  const removeWaypoint = (i) =>
    setWaypoints((w) => w.filter((_, idx) => idx !== i))

  const clearOutputs = () => { setRoutes([]); setRouteInfo(null); setCompareData(null); setErr('') }

  const runFindRoute = async () => {
    clearOutputs(); setBusy(true)
    try {
      const r = await api.findRoute(start, end, algorithm, vehicle, optMode, blockedEdgePayload())
      setRoutes([{ coordinates: r.coordinates, primary: true, color: '#0366d6' }])
      setRouteInfo(r)
      refreshHistory()
    } catch (e) { setErr(String(e.message || e)) }
    setBusy(false)
  }

  const runFindMulti = async () => {
    clearOutputs(); setBusy(true)
    try {
      const r = await api.findMultiRoute(start, waypoints, vehicle, optMode, returnToStart, blockedEdgePayload())
      setRoutes([{ coordinates: r.coordinates, primary: true, color: '#0366d6' }])
      setRouteInfo({
        ...r,
        algorithm: r.method,
        segments: r.legs.map((l, i) => ({
          name: `Chặng ${i + 1}: ${l.from_idx === 0 ? 'Xuất phát' : 'Điểm #' + l.from_idx}` +
                ` → ${l.to_idx === 0 ? 'Xuất phát' : 'Điểm #' + l.to_idx}`,
          distance_m: l.cost,
        })),
      })
      refreshHistory()
    } catch (e) { setErr(String(e.message || e)) }
    setBusy(false)
  }

  const runCompare = async () => {
    clearOutputs(); setBusy(true)
    try {
      const r = await api.compare(start, end, vehicle, optMode, blockedEdgePayload())
      setRoutes([
        { coordinates: r.dijkstra.coordinates, primary: true, color: '#0366d6' },
        { coordinates: r.astar.coordinates, primary: false, color: '#28a745', dash: true },
      ])
      setCompareData(r)
      refreshHistory()
    } catch (e) { setErr(String(e.message || e)) }
    setBusy(false)
  }

  const runAlternatives = async () => {
    clearOutputs(); setBusy(true)
    try {
      const route = await api.findRoute(start, end, algorithm, vehicle, optMode, blockedEdgePayload())
      setRoutes([{ coordinates: route.coordinates, primary: true, color: '#0366d6' }])
      setRouteInfo({
        ...route,
        algorithm: `Tuyến tối ưu (tránh ${blockedEdges.length} đoạn chặn)`,
      })
      refreshHistory()
    } catch (e) { setErr(String(e.message || e)) }
    setBusy(false)
  }
  const onTrafficChange = async (factor, frac) => {
    try { await api.setTraffic(factor, frac) } catch (e) { console.error(e) }
  }
  const onTrafficReset = async () => { try { await api.resetTraffic() } catch (e) { console.error(e) } }

  return (
    <div className="app">
      <div className={'sidebar ' + (busy ? 'loading' : '')}>
        <div className="header">
          <span className="icon">🛵</span>
          <h1>Shipper Route Optimizer — Hà Nội</h1>
        </div>

        {err && <div className="error">⚠ {err}</div>}
        {busy && <div className="info">Đang tính toán...</div>}

        <ControlPanel
          mode={mode} setMode={(m) => { setMode(m); clearOutputs() }}
          start={start} end={end} waypoints={waypoints}
          setStart={setStart} setEnd={setEnd}
          removeWaypoint={removeWaypoint}
          algorithm={algorithm} setAlgorithm={setAlgorithm}
          vehicle={vehicle} setVehicle={setVehicle}
          optMode={optMode} setOptMode={setOptMode}
          returnToStart={returnToStart} setReturnToStart={setReturnToStart}
          onFindRoute={runFindRoute}
          onFindMulti={runFindMulti}
          onCompare={runCompare}
          onAlternatives={runAlternatives}
          blockMode={blockMode}
          setBlockMode={setBlockMode}
          blockedEdges={blockedEdges}
          setBlockedEdges={setBlockedEdges}
          onTrafficChange={onTrafficChange}
          onTrafficReset={onTrafficReset}
          busy={busy}
        />

        {compareData && <ComparisonView data={compareData} />}
        {routeInfo && <RouteInfo result={routeInfo} />}
        <HistoryPanel refreshKey={historyKey} />
      </div>

      <div className="map-wrap">
        <MapView
          start={start} end={end} waypoints={waypoints}
          routes={routes}
          blockedEdges={blockedEdges}
          onMapClick={handleMapClick}
          blockMode={blockMode}
        />
        <div className="legend">
          <div className="item"><span className="dot" style={{ background: '#28a745', width: 10, height: 10, borderRadius: '50%' }}></span>Xuất phát</div>
          <div className="item"><span className="dot" style={{ background: '#cb2431', width: 10, height: 10, borderRadius: '50%' }}></span>Đến</div>
          <div className="item"><span className="dot" style={{ background: '#f0a020', width: 10, height: 10, borderRadius: '50%' }}></span>Điểm giao</div>
        </div>
      </div>
    </div>
  )
}
