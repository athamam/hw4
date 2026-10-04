import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function CreateAccount() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    try {
      await signup({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
      })
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
        <h1>Join Campus Customs</h1>
        <p className="muted">Create an account so our chat helper remembers your favorites.</p>
        <div className="row">
          <label>
            First name
            <input value={form.first_name} onChange={update('first_name')} required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update('last_name')} required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Email
          <input type="email" value={form.email} onChange={update('email')} required autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={update('password')}
            required minLength={8} autoComplete="new-password" />
        </label>
        <label>
          Confirm password
          <input type="password" value={form.confirm} onChange={update('confirm')}
            required minLength={8} autoComplete="new-password" />
        </label>
        <button type="submit" className="btn btn-block" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
        {error && <p className="error">{error}</p>}
        <p className="muted">Already have an account? <Link to="/login" className="link">Log in</Link></p>
      </form>
    </section>
  )
}
