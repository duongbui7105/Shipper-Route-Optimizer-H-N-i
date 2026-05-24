// Tách layer API ra khỏi UI (đáp ứng yêu cầu kiến trúc tách UI/logic/data)
const BASE = '/api'

async function post(path, body) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function get(path) {
  const r = await fetch(BASE + path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function del(path) {
  const r = await fetch(BASE + path, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export const api = {
  findRoute: (start, end, algorithm, vehicle, mode) =>
    post('/route', { start, end, algorithm, vehicle, mode }),

  findMultiRoute: (start, waypoints, vehicle, mode, return_to_start = false) =>
    post('/route/multi', { start, waypoints, vehicle, mode, return_to_start }),

  compare: (start, end, vehicle, mode) =>
    post('/route/compare', { start, end, vehicle, mode }),

  alternatives: (start, end, k = 3, vehicle = 'motorbike', mode = 'time') =>
    post('/route/alternatives', { start, end, k, vehicle, mode }),

  setTraffic: (global_factor, random_fraction = 0) =>
    post('/traffic/simulate', { global_factor, random_fraction }),

  resetTraffic: () => post('/traffic/reset', {}),

  history: () => get('/history'),
  clearHistory: () => del('/history'),
  vehicles: () => get('/vehicles'),

  geocode: (q) => get('/geocode?q=' + encodeURIComponent(q)),
}
