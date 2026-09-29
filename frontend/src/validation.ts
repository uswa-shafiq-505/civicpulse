export function validateComplaint(text: string, location: string): Record<string, string> {
  const errors: Record<string, string> = {}
  const t = text.trim().length
  const l = location.trim().length
  if (t < 10 || t > 2000) errors.text = 'Describe the problem in 10–2000 characters.'
  if (l < 3 || l > 200) errors.location = 'Location must be 3–200 characters.'
  return errors
}