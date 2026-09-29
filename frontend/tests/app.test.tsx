import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SubmitPage from '../src/pages/SubmitPage'
import DashboardPage from '../src/pages/DashboardPage'
import StatsPage from '../src/pages/StatsPage'
import { ErrorBoundary } from '../src/components/ErrorBoundary'
import { ApiError, submitComplaint } from '../src/api/client'
import { validateComplaint } from '../src/validation'
import { json, mockFetch, sample } from './helpers'

afterEach(() => vi.unstubAllGlobals())

describe('validation', () => {
  it('mirrors server length rules', () => {
    expect(validateComplaint('short', 'ab')).toEqual({ text: expect.any(String), location: expect.any(String) })
    expect(validateComplaint('A valid complaint text', 'Street 12')).toEqual({})
  })
})

describe('SubmitPage', () => {
  it('blocks invalid input without calling the API', async () => {
    const f = mockFetch(() => json({}))
    render(<SubmitPage />)
    await userEvent.type(screen.getByLabelText(/describe the problem/i), 'tiny')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(await screen.findByText(/10–2000 characters/)).toBeInTheDocument()
    expect(f).not.toHaveBeenCalled()
  })

  it('shows category, priority, summary and provider after success', async () => {
    mockFetch(() => json({ ...sample, status: 'open' }, 201))
    render(<SubmitPage />)
    await userEvent.type(screen.getByLabelText(/describe the problem/i), 'Water pipe burst near Street 12')
    await userEvent.type(screen.getByLabelText(/location/i), 'Street 12, Islamabad')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    const card = await screen.findByTestId('result')
    expect(card).toHaveTextContent('water'); expect(card).toHaveTextContent('high')
    expect(card).toHaveTextContent('Burst water main on Street 12'); expect(card).toHaveTextContent('rules')
  })
})

describe('DashboardPage', () => {
  it("surfaces the server's 409 message verbatim", async () => {
    const msg = 'Invalid transition: resolved -> open' // VERIFY: use the wording your backend actually returns
    mockFetch((url, init) => {
      if (init?.method === 'PATCH') return json({ detail: msg }, 409)
      return json({ items: [sample], total: 1, page: 1, page_size: 10 })
    })
    render(<DashboardPage />)
    await screen.findByText('Burst water main on Street 12')
    await userEvent.click(screen.getByRole('button', { name: 'open' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(msg)
  })

  it('sends filter values as query params and resets to page 1', async () => {
    const f = mockFetch(() => json({ items: [], total: 0, page: 1, page_size: 10 }))
    render(<DashboardPage />)
    await userEvent.selectOptions(await screen.findByLabelText('Category'), 'water')
    await waitFor(() => expect(f.mock.calls.some(c => String(c[0]).includes('category=water') && String(c[0]).includes('page=1'))).toBe(true))
  })
})

describe('StatsPage', () => {
  it('renders the X-Cache header state', async () => {
    mockFetch(url => url.includes('/stats') ? json({ total: 3 }, 200, { 'X-Cache': 'HIT' }) : json({ active: 'rules' }))
    render(<StatsPage />)
    await waitFor(() => expect(screen.getByTestId('cache-status')).toHaveTextContent('HIT'))
  })
})

describe('ErrorBoundary and client', () => {
  it('renders a fallback when a child throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const Boom = () => { throw new Error('kaboom') }
    render(<ErrorBoundary><Boom /></ErrorBoundary>)
    expect(screen.getByRole('alert')).toHaveTextContent('kaboom')
  })

  it('turns a 429 into an ApiError with Retry-After', async () => {
    mockFetch(() => json({ detail: 'rate limited' }, 429, { 'Retry-After': '12' }))
    await expect(submitComplaint({ text: 'x'.repeat(20), location: 'Street 12' })).rejects.toMatchObject({ status: 429, retryAfter: 12 })
    expect(ApiError).toBeDefined()
  })
})