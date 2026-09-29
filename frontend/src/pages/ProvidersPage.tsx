import { useEffect, useState } from 'react'
import { getProviders } from '../api/client'
import type { JsonObject } from '../api/types'

export default function ProvidersPage() {
  const [data, setData] = useState<JsonObject | null>(null)

  async function load() {
    const r = await getProviders()
    setData(r.data)
  }

  useEffect(() => { void load() }, [])

  if (!data) return <p>Loading…</p>

  const recent = (data.recent_triages as Array<Record<string, unknown>>) ?? []

  return (
    <section>
      <h1>Triage providers</h1>
      <p>Active provider: <strong>{String(data.active_provider)}</strong></p>
      <h3>Recent triages</h3>
      <table>
        <thead><tr><th>Provider</th><th>Latency (ms)</th><th>Fallback</th></tr></thead>
        <tbody>
          {recent.map((r, i) => (
            <tr key={i}>
              <td>{String(r.provider)}</td>
              <td>{String(r.latency_ms)}</td>
              <td>{String(r.fallback)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={load}>Refresh</button>
    </section>
  )
}
