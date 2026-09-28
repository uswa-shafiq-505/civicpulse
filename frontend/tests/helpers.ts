import { vi } from 'vitest'

export const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...headers } })

export function mockFetch(handler: (url: string, init?: RequestInit) => Response) {
  const fn = vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))
  vi.stubGlobal('fetch', fn)
  return fn
}

export const sample = {
  id: '11111111-1111-1111-1111-111111111111', text: 'Water pipe burst near Street 12', location: 'Street 12',
  reporter_contact: null, category: 'water', priority: 'high', status: 'resolved', ai_summary: 'Burst water main on Street 12',
  triaged_by: 'rules', triage_latency_ms: 3, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
}