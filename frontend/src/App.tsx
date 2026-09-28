import { useEffect, useState } from 'react'
import { getStats } from './api/client'

export default function App() {
  const [out, setOut] = useState('loading…')
  useEffect(() => {
    getStats()
      .then(r => setOut(`X-Cache=${r.headers.get('X-Cache')}\n${JSON.stringify(r.data, null, 2)}`))
      .catch(e => setOut(String(e)))
  }, [])
  return <pre>{out}</pre>
}