import { useState } from 'react'
import { api } from '../api/client'

export default function SearchBox({ placeholder, onPick }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!q.trim()) return
    setLoading(true)
    try {
      const r = await api.geocode(q)
      setResults(r)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  return (
    <div>
      <div className="row">
        <input
          type="text"
          placeholder={placeholder}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
        />
        <button className="btn btn-secondary" style={{ flex: 0 }} onClick={search} disabled={loading}>
          🔍
        </button>
      </div>
      {results.length > 0 && (
        <div className="geo-results">
          {results.map((r, i) => (
            <div
              key={i}
              className="item"
              onClick={() => {
                onPick({ lat: parseFloat(r.lat), lon: parseFloat(r.lon), label: r.display_name })
                setResults([])
                setQ(r.display_name.split(',').slice(0, 2).join(','))
              }}
            >
              {r.display_name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
