import { useEffect, useState } from 'react'
import { api } from '../api/client'
import SearchBox from './SearchBox'

export default function ControlPanel({
  mode, setMode,
  start, end, waypoints,
  setStart, setEnd,
  removeWaypoint,
  algorithm, setAlgorithm,
  vehicle, setVehicle,
  optMode, setOptMode,
  returnToStart, setReturnToStart,
  onFindRoute, onFindMulti, onCompare, onAlternatives,
  onTrafficChange, onTrafficReset,
  busy,
}) {
  const [vehicles, setVehicles] = useState({})
  const [traffic, setTraffic] = useState(1.0)
  const [congestion, setCongestion] = useState(0)

  useEffect(() => { api.vehicles().then(setVehicles).catch(() => {}) }, [])

  return (
    <>
      <div className="tabs">
        <div className={'tab ' + (mode === 'single' ? 'active' : '')} onClick={() => setMode('single')}>1 điểm</div>
        <div className={'tab ' + (mode === 'multi' ? 'active' : '')} onClick={() => setMode('multi')}>Nhiều điểm</div>
        <div className={'tab ' + (mode === 'compare' ? 'active' : '')} onClick={() => setMode('compare')}>So sánh</div>
        <div className={'tab ' + (mode === 'alt' ? 'active' : '')} onClick={() => setMode('alt')}>Tuyến thay thế</div>
      </div>

      <div className="section">
        <h3>📍 Điểm đi & đến</h3>
        <div className="info" style={{ marginTop: 0 }}>
          Click trên bản đồ hoặc tìm địa chỉ. Click đầu = điểm xuất phát,
          các click sau = điểm đến hoặc điểm giao hàng.
        </div>
        <label>Tìm địa chỉ</label>
        <SearchBox
          placeholder="VD: Hồ Hoàn Kiếm, Mỹ Đình..."
          onPick={(p) => { if (!start) setStart(p); else setEnd(p) }}
        />

        {start && (
          <div className="point-pill">
            <span className="dot" style={{ background: '#28a745' }}></span>
            <strong>Xuất phát:</strong>{' '}
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
              {start.label || `${start.lat.toFixed(4)}, ${start.lon.toFixed(4)}`}
            </span>
            <span className="x" onClick={() => setStart(null)}>✕</span>
          </div>
        )}
        {end && (
          <div className="point-pill">
            <span className="dot" style={{ background: '#cb2431' }}></span>
            <strong>Đến:</strong>{' '}
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
              {end.label || `${end.lat.toFixed(4)}, ${end.lon.toFixed(4)}`}
            </span>
            <span className="x" onClick={() => setEnd(null)}>✕</span>
          </div>
        )}
        {mode === 'multi' && waypoints.map((w, i) => (
          <div key={i} className="point-pill">
            <span className="dot" style={{ background: '#f0a020' }}></span>
            <strong>#{i + 1}:</strong>{' '}
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
              {w.label || `${w.lat.toFixed(4)}, ${w.lon.toFixed(4)}`}
            </span>
            <span className="x" onClick={() => removeWaypoint(i)}>✕</span>
          </div>
        ))}
      </div>

      <div className="section">
        <h3>⚙ Tùy chọn</h3>
        <label>Phương tiện</label>
        <select value={vehicle} onChange={(e) => setVehicle(e.target.value)}>
          {Object.entries(vehicles).map(([k, v]) => (
            <option key={k} value={k}>{v.label} ({v.speed_kmh} km/h)</option>
          ))}
        </select>

        <label>Tối ưu theo</label>
        <select value={optMode} onChange={(e) => setOptMode(e.target.value)}>
          <option value="time">Thời gian</option>
          <option value="distance">Quãng đường</option>
        </select>

        {mode === 'single' && (
          <>
            <label>Thuật toán</label>
            <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
              <option value="dijkstra">Dijkstra (tự cài)</option>
              <option value="astar">A* (tự cài)</option>
            </select>
          </>
        )}

        {mode === 'multi' && (
          <label style={{ marginTop: 4 }}>
            <input
              type="checkbox"
              checked={returnToStart}
              onChange={(e) => setReturnToStart(e.target.checked)}
            /> Quay về điểm xuất phát
          </label>
        )}
      </div>

      <div className="section">
        <h3>🚦 Mô phỏng kẹt xe</h3>
        <label>Hệ số chung: <strong>{traffic.toFixed(1)}×</strong></label>
        <input
          type="range" min="0.5" max="3" step="0.1" value={traffic}
          onChange={(e) => { setTraffic(parseFloat(e.target.value)) }}
          onMouseUp={() => onTrafficChange(traffic, congestion)}
          onTouchEnd={() => onTrafficChange(traffic, congestion)}
        />
        <label>Tỉ lệ tuyến kẹt: <strong>{Math.round(congestion * 100)}%</strong></label>
        <input
          type="range" min="0" max="0.3" step="0.02" value={congestion}
          onChange={(e) => setCongestion(parseFloat(e.target.value))}
          onMouseUp={() => onTrafficChange(traffic, congestion)}
          onTouchEnd={() => onTrafficChange(traffic, congestion)}
        />
        <button className="btn btn-secondary" style={{ fontSize: 11, marginTop: 4 }} onClick={() => {
          setTraffic(1.0); setCongestion(0); onTrafficReset()
        }}>Reset</button>
      </div>

      <div className="section">
        <div className="btn-row">
          {mode === 'single' && (
            <button className="btn btn-primary" disabled={!start || !end || busy} onClick={onFindRoute}>
              Tìm đường
            </button>
          )}
          {mode === 'multi' && (
            <button className="btn btn-primary" disabled={!start || waypoints.length === 0 || busy} onClick={onFindMulti}>
              Tối ưu ({waypoints.length} điểm)
            </button>
          )}
          {mode === 'compare' && (
            <button className="btn btn-primary" disabled={!start || !end || busy} onClick={onCompare}>
              So sánh Dijkstra vs A*
            </button>
          )}
          {mode === 'alt' && (
            <button className="btn btn-primary" disabled={!start || !end || busy} onClick={onAlternatives}>
              Tìm 3 tuyến thay thế
            </button>
          )}
        </div>
      </div>
    </>
  )
}
