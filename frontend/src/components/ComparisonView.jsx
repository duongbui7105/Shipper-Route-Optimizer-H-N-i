export default function ComparisonView({ data }) {
  if (!data) return null
  return (
    <div className="section">
      <h3>⚖ So sánh Dijkstra vs A*</h3>
      <div className="compare-box">
        <div>
          <div className="label">Dijkstra</div>
          <div className="val">{data.dijkstra.runtime_ms} ms</div>
          <div style={{ fontSize: 11, color: '#586069' }}>{data.dijkstra.visited_nodes.toLocaleString()} nodes</div>
        </div>
        <div>
          <div className="label">A*</div>
          <div className="val">{data.astar.runtime_ms} ms</div>
          <div style={{ fontSize: 11, color: '#586069' }}>{data.astar.visited_nodes.toLocaleString()} nodes</div>
        </div>
      </div>
      <div style={{ fontSize: 12, marginTop: 8 }}>
        {data.same_path ? '✅ Cùng tuyến đường' : '⚠️ Khác tuyến đường'}
        {data.speedup && <> · A* nhanh hơn <strong>{data.speedup}×</strong></>}
      </div>
      <div style={{ fontSize: 11, color: '#6a737d', marginTop: 6 }}>
        Trên bản đồ: <span style={{ color: '#0366d6' }}>━━━</span> Dijkstra ·{' '}
        <span style={{ color: '#28a745' }}>- - -</span> A*
      </div>
    </div>
  )
}
