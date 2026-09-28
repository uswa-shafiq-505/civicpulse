import { useCallback, useEffect, useState } from 'react'
import { ApiError, listComplaints, updateStatus } from '../api/client'
import { CATEGORIES, PRIORITIES, STATUSES, type Complaint, type ComplaintFilters, type Status } from '../api/types'
import { Alert } from '../components/Alert'

const PAGE_SIZE = 10

export default function DashboardPage() {
  const [filters, setFilters] = useState<ComplaintFilters>({})
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<Complaint[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await listComplaints(page, PAGE_SIZE, filters)
      setItems(r.data.items); setTotal(r.data.total)
    } catch (e) { setError(e instanceof ApiError ? e.message : 'Failed to load complaints.') }
    finally { setLoading(false) }
  }, [page, filters])

  useEffect(() => { void load() }, [load])

  async function advance(id: string, to: Status) {
    setError(null); setBusy(id)
    try { await updateStatus(id, to); await load() }
    catch (e) { setError(e instanceof ApiError ? e.message : 'Status update failed.') } // server's 409 text, verbatim
    finally { setBusy(null) }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const setFilter = (k: keyof ComplaintFilters, v: string) => { setPage(1); setFilters(f => ({ ...f, [k]: v })) }

  return (
    <section>
      <h1>Operations dashboard</h1>
      <div className="filters">
        <select aria-label="Category" value={filters.category ?? ''} onChange={e => setFilter('category', e.target.value)}>
          <option value="">All categories</option>{CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <select aria-label="Priority" value={filters.priority ?? ''} onChange={e => setFilter('priority', e.target.value)}>
          <option value="">All priorities</option>{PRIORITIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <select aria-label="Status" value={filters.status ?? ''} onChange={e => setFilter('status', e.target.value)}>
          <option value="">All statuses</option>{STATUSES.map(c => <option key={c}>{c}</option>)}
        </select>
      </div>
      {error && <Alert>{error}</Alert>}
      {loading ? <p>Loading…</p> : (
        <table>
          <thead><tr><th>Summary</th><th>Category</th><th>Priority</th><th>Status</th><th>Triaged by</th><th>Move to</th></tr></thead>
          <tbody>
            {items.map(c => (
              <tr key={c.id}>
                <td title={c.text}>{c.ai_summary ?? c.text.slice(0, 80)}</td>
                <td>{c.category}</td><td>{c.priority}</td><td>{c.status}</td><td>{c.triaged_by}</td>
                <td>
                  {/* Every status except the current one is offered. Whether the move is legal is the
                      server's decision — we surface its 409 message instead of duplicating the rules. */}
                  {STATUSES.filter(s => s !== c.status).map(s => (
                    <button key={s} disabled={busy === c.id} onClick={() => void advance(c.id, s)}>{s}</button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Prev</button>
        <span>Page {page} of {pages} ({total} total)</span>
        <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}>Next</button>
      </div>
    </section>
  )
}