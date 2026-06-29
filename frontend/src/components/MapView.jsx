import { MapContainer, TileLayer, Marker, Polyline, useMapEvents, Popup } from 'react-leaflet'
import L from 'leaflet'

// Fix icon path cho Leaflet trong Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function colorIcon(color) {
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

const ICONS = {
  start: colorIcon('#28a745'),
  end: colorIcon('#cb2431'),
  waypoint: colorIcon('#f0a020'),
}

function ClickHandler({ onClick }) {
  useMapEvents({ click: (e) => onClick(e.latlng) })
  return null
}

export default function MapView({
  start, end, waypoints, routes,
  blockedEdges = [], onMapClick,
  blockMode = false,
}) {
  // Hà Nội center
  const center = [21.0285, 105.8542]
  return (
    <MapContainer
      className={blockMode ? 'block-mode' : ''}
      center={center} zoom={12} scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onClick={onMapClick} />

      {start && (
        <Marker position={[start.lat, start.lon]} icon={ICONS.start}>
          <Popup>Điểm xuất phát<br/>{start.label || ''}</Popup>
        </Marker>
      )}
      {end && (
        <Marker position={[end.lat, end.lon]} icon={ICONS.end}>
          <Popup>Điểm đến<br/>{end.label || ''}</Popup>
        </Marker>
      )}
      {waypoints && waypoints.map((w, i) => (
        <Marker key={i} position={[w.lat, w.lon]} icon={ICONS.waypoint}>
          <Popup>Điểm giao #{i + 1}<br/>{w.label || ''}</Popup>
        </Marker>
      ))}

      {routes && routes.map((r, i) => (
        <Polyline
          key={i}
          positions={r.coordinates}
          pathOptions={{
            color: r.color || '#0366d6',
            weight: r.primary ? 6 : 4,
            opacity: r.primary ? 0.85 : 0.55,
            dashArray: r.dash ? '8 8' : null,
          }}
        />
      ))}

      {blockedEdges.map((edge, i) => (
        <Polyline
          key={`blocked-${i}-${edge.u}-${edge.v}-${edge.key}`}
          positions={edge.coordinates}
          pathOptions={{
            color: '#cb2431',
            weight: 7,
            opacity: 0.9,
            dashArray: '10 6',
          }}
        />
      ))}
    </MapContainer>
  )
}
