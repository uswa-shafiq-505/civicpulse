import { useEffect, useState } from 'react'
import { ApiError, submitComplaint } from '../api/client'
import type { Complaint } from '../api/types'
import { validateComplaint } from '../validation'
import { Alert } from '../components/Alert'

function useElapsed(active: boolean) {
  const [s, setS] = useState(0)
  useEffect(() => {
    if (!active) return
    setS(0)
    const t = setInterval(() => setS(x => x + 1), 1000)
    return () => clearInterval(t)
  }, [active])
  return s
}

export default function SubmitPage() {
  const [text, setText] = useState('')
  const [location, setLocation] = useState('')
  const [contact, setContact] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Complaint | null>(null)
  const elapsed = useElapsed(loading)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setServerError(null); setResult(null)
    const v = validateComplaint(text, location)
    setErrors(v)
    if (Object.keys(v).length) return
    setLoading(true)
    try {
      const r = await submitComplaint({ text: text.trim(), location: location.trim(), reporter_contact: contact.trim() || null })
      setResult(r.data)
      setText(''); setLocation(''); setContact('')
    } catch (err) {
      if (err instanceof ApiError) { setErrors(err.fieldErrors); setServerError(err.message) }
      else setServerError('Unexpected error.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h1>Report a problem</h1>
      <form onSubmit={onSubmit} noValidate>
        <label>Describe the problem
          <textarea value={text} onChange={e => setText(e.target.value)} rows={5} aria-invalid={!!errors.text} />
        </label>
        {errors.text && <p className="field-error">{errors.text}</p>}
        <label>Location
          <input value={location} onChange={e => setLocation(e.target.value)} aria-invalid={!!errors.location} />
        </label>
        {errors.location && <p className="field-error">{errors.location}</p>}
        <label>Contact (optional)
          <input value={contact} onChange={e => setContact(e.target.value)} />
        </label>
        <button type="submit" disabled={loading}>{loading ? `Triaging with AI… ${elapsed}s` : 'Submit'}</button>
        {loading && <p className="hint">AI triage can take a few seconds. Please don’t close this page.</p>}
      </form>
      {serverError && <Alert>{serverError}</Alert>}
      {result && (
        <div className="card" data-testid="result">
          <h2>Received</h2>
          <dl>
            <dt>Category</dt><dd>{result.category}</dd>
            <dt>Priority</dt><dd>{result.priority}</dd>
            <dt>AI summary</dt><dd>{result.ai_summary ?? '—'}</dd>
            <dt>Triaged by</dt><dd>{result.triaged_by}</dd>
          </dl>
        </div>
      )}
    </section>
  )
}