import { useEffect, useState } from 'react'
import { getStats } from '../api/client'
import type { JsonObject } from '../api/types'

export default function StatsPage() {
  const [stats, setStats] = useState<JsonObject | null>(null)
  const [cacheStatus, setCacheStatus] = useState<string>('')

  async function load() {
    const r = await getStats()
    setStats(r.data)
    setCacheStatus(r.headers.get('X-Cache') ?? 'unknown')
  }

  useEffect(() => { void load() }, [])

  if (!stats) return <p>Loading…</p>

  const byCategory = (stats.by_category as Record<string, number>) ?? {}
  const byPriority = (stats.by_priority as Record<string, number>) ?? {}

  return (
    <section>
      <h1>Statistics</h1>
      <p>Cache: <strong data-testid="cache-status" className={`badge ${cacheStatus.toUpperCase()}`}>{cacheStatus.toUpperCase()}</strong></p>
      <p>Total complaints: {stats.total as number}</p>
      <h3>By category</h3>
      <ul>{Object.entries(byCategory).map(([k, v]) => <li key={k}>{k}: {v}</li>)}</ul>
      <h3>By priority</h3>
      <ul>{Object.entries(byPriority).map(([k, v]) => <li key={k}>{k}: {v}</li>)}</ul>
      <button onClick={load}>Refresh</button>
    </section>
  )
}