import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ErrorBanner from '../components/ErrorBanner'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const DEMO = [
    { label: 'Employee', u: 'alice', p: 'password123' },
    { label: 'Manager', u: 'charlie', p: 'password123' },
    { label: 'App Owner', u: 'eve', p: 'password123' },
    { label: 'IT Admin', u: 'grace', p: 'password123' },
    { label: 'Auditor', u: 'ivan', p: 'password123' },
  ]

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (!form.username.trim() || !form.password) {
      setError('Username and password are required')
      return
    }
    setLoading(true)
    try {
      await login(form.username.trim(), form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={page}>
      <div style={card}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 48 }}>🔐</div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginTop: 8 }}>Access Review System</h1>
          <p style={{ color: '#718096', marginTop: 4, fontSize: 14 }}>Sign in to continue</p>
        </div>
        <ErrorBanner message={error} />
        <form onSubmit={handleSubmit}>
          <div style={field}>
            <label style={lbl}>Username</label>
            <input style={inp} value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              autoFocus autoComplete="username" />
          </div>
          <div style={field}>
            <label style={lbl}>Password</label>
            <input style={inp} type="password" value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              autoComplete="current-password" />
          </div>
          <button type="submit" disabled={loading} style={submitBtn}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <div style={{ marginTop: 24, borderTop: '1px solid #e2e8f0', paddingTop: 16 }}>
          <p style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>Demo accounts (password: password123)</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {DEMO.map(d => (
              <button key={d.u} onClick={() => setForm({ username: d.u, password: d.p })}
                style={demoBtn}>
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const page = {
  minHeight: '100vh', display: 'flex', alignItems: 'center',
  justifyContent: 'center', background: '#f0f4f8',
}
const card = {
  background: '#fff', borderRadius: 12, padding: '36px 40px',
  width: '100%', maxWidth: 420, boxShadow: '0 4px 24px rgba(0,0,0,0.1)',
}
const field = { marginBottom: 16 }
const lbl = { display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#4a5568' }
const inp = {
  width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0',
  borderRadius: 6, fontSize: 14, outline: 'none',
}
const submitBtn = {
  width: '100%', padding: '11px', background: '#3182ce', color: '#fff',
  border: 'none', borderRadius: 6, fontSize: 15, fontWeight: 600,
  cursor: 'pointer', marginTop: 4,
}
const demoBtn = {
  padding: '4px 10px', background: '#ebf8ff', color: '#2b6cb0',
  border: '1px solid #bee3f8', borderRadius: 5, cursor: 'pointer', fontSize: 12,
}
