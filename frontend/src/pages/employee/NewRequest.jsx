import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api'
import ErrorBanner from '../../components/ErrorBanner'

export default function NewRequest() {
  const navigate = useNavigate()
  const [apps, setApps] = useState([])
  const [form, setForm] = useState({ application_id: '', access_level: '', justification: '', expiry_date: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => { api.get('/applications').then(r => setApps(r.data.applications)) }, [])

  const selectedApp = apps.find(a => String(a.id) === String(form.application_id))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (!form.application_id) return setError('Please select an application')
    if (!form.access_level) return setError('Please select an access level')
    if (!form.justification.trim()) return setError('Justification is required')
    setLoading(true)
    try {
      const payload = {
        application_id: Number(form.application_id),
        access_level: form.access_level,
        justification: form.justification.trim(),
      }
      if (form.expiry_date) payload.expiry_date = form.expiry_date
      await api.post('/requests', payload)
      setSuccess(true)
      setTimeout(() => navigate('/my-requests'), 1500)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit request')
    } finally {
      setLoading(false)
    }
  }

  if (success) return (
    <div style={successBox}>
      ✅ Request submitted! Redirecting to your requests…
    </div>
  )

  return (
    <div>
      <h2 style={{ marginBottom: 4 }}>New Access Request</h2>
      <p style={{ color: '#718096', marginBottom: 20 }}>Submit a request for access to an application.</p>
      <div style={card}>
        <ErrorBanner message={error} />
        <form onSubmit={handleSubmit}>
          <Field label="Application *">
            <select style={inp} value={form.application_id}
              onChange={e => setForm(f => ({ ...f, application_id: e.target.value, access_level: '' }))}>
              <option value="">— Select an application —</option>
              {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          {selectedApp && (
            <Field label="Access Level *">
              <select style={inp} value={form.access_level}
                onChange={e => setForm(f => ({ ...f, access_level: e.target.value }))}>
                <option value="">— Select level —</option>
                {selectedApp.access_levels.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
          )}
          <Field label="Justification *">
            <textarea style={{ ...inp, minHeight: 90, resize: 'vertical' }}
              placeholder="Explain why you need this access…"
              value={form.justification}
              onChange={e => setForm(f => ({ ...f, justification: e.target.value }))} />
          </Field>
          <Field label="Expiry Date (optional)">
            <input type="date" style={inp} value={form.expiry_date}
              onChange={e => setForm(f => ({ ...f, expiry_date: e.target.value }))} />
          </Field>
          <button type="submit" disabled={loading} style={submitBtn}>
            {loading ? 'Submitting…' : 'Submit Request'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#4a5568' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

const card = { background: '#fff', borderRadius: 10, padding: 28, maxWidth: 540, boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const inp = { width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14 }
const submitBtn = {
  width: '100%', padding: 11, background: '#3182ce', color: '#fff',
  border: 'none', borderRadius: 6, fontSize: 15, fontWeight: 600, cursor: 'pointer',
}
const successBox = {
  background: '#f0fff4', border: '1px solid #9ae6b4', borderRadius: 8,
  padding: '20px 24px', color: '#276749', fontSize: 16,
}
