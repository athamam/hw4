import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Welcome back</h1>
        <p className="muted">Log in to pick up your chat where you left off.</p>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            required autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            required autoComplete="current-password" />
        </label>
        <button type="submit" className="btn btn-block" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
        {error && <p className="error">{error}</p>}
        <p className="muted">New here? <Link to="/create-account" className="link">Create an account</Link></p>
      </form>
    </section>
  )
}
