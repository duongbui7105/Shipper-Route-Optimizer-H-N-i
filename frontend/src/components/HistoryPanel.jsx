import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function HistoryPanel({ refreshKey }) {
  const [items, setItems] = useState([])

  const load = async () => {
    try { setItems(await api.history()) } catch (e) { console.error(e) }
  }
  useEffect(() => { load() }, [refreshKey])

  const clearAll = async () => {
    if (!confirm('Xóa toàn bộ lịch sử?')) return
    await api.clearHistory()
    load()
  }

  return (
    <div className="section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>📜 Lịch sử ({items.length})</h3>
        {items.length > 0 && (
          <button className="btn btn-secondary" style={{ padding: '3px 8px', fontSize: 11 }} onClick={clearAll}>
            Xóa
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <div style={{ fontSize: 12, color: '#6a737d' }}>Chưa có lịch sử nào.</div>
      ) : (
        items.slice(0, 10).map((h) => (
          <div key={h.id} className="history-item">
            <div>
              <strong>{h.algorithm}</strong> · {(h.distance_m / 1000).toFixed(2)} km · {Math.round(h.time_s / 60)} phút
            </div>
            <div className="when">
              {new Date(h.created_at).toLocaleString('vi-VN')} · {h.vehicle} · {h.mode}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
