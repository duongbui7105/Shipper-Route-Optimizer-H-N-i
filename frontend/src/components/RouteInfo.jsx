function fmtDist(m) {
  if (m < 1000) return `${Math.round(m)} m`
  return `${(m / 1000).toFixed(2)} km`
}
function fmtTime(s) {
  if (s < 60) return `${Math.round(s)} giây`
  const m = Math.floor(s / 60), r = Math.round(s % 60)
  if (m < 60) return `${m} phút ${r} s`
  const h = Math.floor(m / 60)
  return `${h} h ${m % 60} phút`
}

export default function RouteInfo({ result }) {
  if (!result) return null
  return (
    <div className="section">
      <h3>🗺 Kết quả</h3>
      <div className="metric"><span>Tổng quãng đường</span><span className="v">{fmtDist(result.distance_m)}</span></div>
      <div className="metric"><span>Thời gian ước tính</span><span className="v">{fmtTime(result.time_s)}</span></div>
      {result.algorithm && (
        <div className="metric"><span>Thuật toán</span><span className="v">{result.algorithm}</span></div>
      )}
      {result.runtime_ms !== undefined && (
        <div className="metric"><span>Thời gian xử lý</span><span className="v">{result.runtime_ms} ms</span></div>
      )}
      {result.visited_nodes !== undefined && (
        <div className="metric"><span>Nodes đã duyệt</span><span className="v">{result.visited_nodes.toLocaleString()}</span></div>
      )}

      {result.segments && result.segments.length > 0 && (
        <>
          <h3 style={{ marginTop: 12 }}>📋 Danh sách chặng</h3>
          <div className="segments-list">
            {result.segments.map((s, i) => (
              <div key={i} className="seg">
                <strong>{i + 1}.</strong> {s.name} <span style={{ float: 'right' }}>{fmtDist(s.distance_m)}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
