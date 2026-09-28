export const CATEGORIES = ['water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other'] as const
export const PRIORITIES = ['high', 'normal', 'low'] as const
export const STATUSES = ['open', 'in_progress', 'resolved', 'rejected'] as const

export type Category = (typeof CATEGORIES)[number]
export type Priority = (typeof PRIORITIES)[number]
export type Status = (typeof STATUSES)[number]

export interface Complaint {
  id: string
  text: string
  location: string
  reporter_contact: string | null
  category: Category
  priority: Priority
  status: Status
  ai_summary: string | null
  triaged_by: string
  triage_latency_ms: number | null
  created_at: string
  updated_at: string
}

export interface ComplaintCreate { text: string; location: string; reporter_contact?: string | null }
export interface ComplaintPage { items: Complaint[]; total: number; page: number; page_size: number }
export interface ComplaintFilters { category?: Category | ''; priority?: Priority | ''; status?: Status | '' }

// Shape of /api/stats and /api/meta/providers is rendered generically (see pages) so a backend
// change cannot break the UI silently.
export type JsonObject = Record<string, unknown>