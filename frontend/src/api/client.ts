import type { Complaint, ComplaintCreate, ComplaintFilters, ComplaintPage, JsonObject, Status } from './types'

const BASE = '/api' // relative on purpose: works behind nginx, ingress and the Vite dev proxy

export class ApiError extends Error {
  status: number
  fieldErrors: Record<string, string>
  retryAfter?: number
  constructor(status: number, message: string, fieldErrors: Record<string, string> = {}, retryAfter?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
    this.retryAfter = retryAfter
  }
}

export interface ApiResult<T> { data: T; headers: Headers }

function toError(status: number, body: unknown, res: Response): ApiError {
  const b = (body && typeof body === 'object' ? body : {}) as JsonObject
  const fields: Record<string, string> = {}
  let message = `Request failed (${status})`

  if (Array.isArray(b.errors)) {
    for (const e of b.errors as JsonObject[]) {
      const f = typeof e.field === 'string' ? e.field : ''
      if (f) fields[f] = String(e.message ?? 'invalid')
    }
    message = typeof b.detail === 'string' ? b.detail : 'Please fix the highlighted fields.'
  } else if (typeof b.detail === 'string') {
    message = b.detail
  }

  const ra = res.headers.get('Retry-After')
  const retryAfter = ra ? Number(ra) : undefined
  if (status === 429) message = `Too many requests.${retryAfter ? ` Try again in ${retryAfter}s.` : ''}`
  return new ApiError(status, message, fields, retryAfter)
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.')
  }
  const text = await res.text()
  const body: unknown = text ? JSON.parse(text) : null
  if (!res.ok) throw toError(res.status, body, res)
  return { data: body as T, headers: res.headers }
}

export const submitComplaint = (payload: ComplaintCreate) =>
  request<Complaint>('/complaints', { method: 'POST', body: JSON.stringify(payload) })

export function listComplaints(page: number, pageSize: number, f: ComplaintFilters) {
  const q = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (f.category) q.set('category', f.category)
  if (f.priority) q.set('priority', f.priority)
  if (f.status) q.set('status', f.status)
  return request<ComplaintPage>(`/complaints?${q.toString()}`)
}

export const updateStatus = (id: string, status: Status) =>
  request<Complaint>(`/complaints/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) })

export const getStats = () => request<JsonObject>('/stats')
export const getProviders = () => request<JsonObject>('/meta/providers')