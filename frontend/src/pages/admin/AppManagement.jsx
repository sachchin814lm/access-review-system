import React, { useEffect, useState } from 'react'
import api from '../../api'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

export default function AppManagement() {
  const [apps, setApps] = useState([])
  const [owners, setOwners] = useState([])
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState({})
  const [levelsStr, setLevelsStr] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const load = () => Promise.all([
    api.get('/applications').then(r => setApps(r.data.applications)),
    api.get('/users').then(r => setOwners(r.data.users.filter(u => u.role === 'app_owner'))),
  ])
  useEffect(load, [])

  const openCreate = () => {
    setModal({ type: 'create' })
    setForm({ name: '', description: '', owner_id: '', is_active: true })
    setLevelsStr('Read, Write, Admin')
    setError('')
  }
  const openEdit = app => {
    setModal({ type: 'edit', app })
    setForm({ ...app })
    setLevelsStr((app.access_levels || []).join(', '))
    setError('')
  }

  const handleSave = async () => {
    setSaving(true); setError('')
    const payload = {
      ...form,
      owner_id: Number(form.owner_id),
      access_levels: levelsStr.split(',').map(s => s.trim()).filter(Boolean),
    }
    try {
      if (modal.type === 'create') {
        await api.post('/applications', payload)
      } else {
        await api.put(`/applications/${modal.app.id}`, payload)
      }
      setModal(null); load()
    } catch (err) {
      setError(err.response?.data?.error || 'Save failed')
    } finally { setSaving(false) }
  }

  const handleDelete = async id => {
    if (!window.confirm('Deactivate this application?')) return
    try { await api.delete(`/applications/${id}`); load() } catch {}
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0 }}>Application Management</h2>
        <button onClick={openCreate} style={createBtn}>+ New Application</button>
      </div>
      <div style={tableWrap}>
        <table style={tbl}>
          <thead><tr>
            <Th>Name</Th><Th>Description</Th><Th>Access Levels</Th><Th>Owner</Th><Th>Status</Th><Th>Actions</Th>
          </tr></thead>
          <tbody>
            {apps.map(a => (
              <tr key={a.id} style={{ borderBottom: '1px solid #e2e8f0', opacity: a.is_active ? 1 : 0.5 }}>
                <Td><strong>{a.name}</strong></Td>
                <Td style={{ fontSize: 13, color: '#718096', maxWidth: 200 }}>{a.description}</Td>
                <Td>{(a.access_levels || []).join(', ')}</Td>
                <Td>{owners.find(o => o.id === a.owner_id)?.full_name || a.owner_id}</Td>
                <Td><span style={{ color: a.is_active ? '#276749' : '#c53030', fontWeight: 600, fontSize: 13 }}>{a.is_active ? 'Active' : 'Inactive'}</span></Td>
                <Td>
                  <button onClick={() => openEdit(a)} style={editBtn}>Edit</button>
                  {a.is_active && <button onClick={() => handleDelete(a.id)} style={delBtn}>Deactivate</button>}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal title={modal.type === 'create' ? '➕ New Application' : '✏️ Edit Application'} onClose={() => setModal(null)}>
          <ErrorBanner message={error} />
          <div style={{ marginBottom: 12 }}>
            <label style={lbl}>Name *</label>
            <input style={inp} value={form.name || ''} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={lbl}>Description</label>
            <input style={inp} value={form.description || ''} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={lbl}>Access Levels * (comma-separated)</label>
            <input style={inp} value={levelsStr} onChange={e => setLevelsStr(e.target.value)} placeholder="Read, Write, Admin" />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={lbl}>Owner *</label>
            <select style={inp} value={form.owner_id || ''} onChange={e => setForm(f => ({ ...f, owner_id: e.target.value }))}>
              <option value="">— Select —</option>
              {owners.map(o => <option key={o.id} value={o.id}>{o.full_name}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button onClick={handleSave} disabled={saving} style={{ ...createBtn, flex: 1 }}>
              {saving ? '…' : 'Save'}
            </button>
            <button onClick={() => setModal(null)} style={grayBtn}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 600 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', fontSize: 14, ...style }}>{children}</td>
const createBtn = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }
const editBtn   = { padding: '4px 10px', background: '#ebf8ff', color: '#2b6cb0', border: 'none', borderRadius: 4, cursor: 'pointer', marginRight: 6, fontSize: 13 }
const delBtn    = { padding: '4px 10px', background: '#fff5f5', color: '#c53030', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13 }
const grayBtn   = { padding: '8px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 6, cursor: 'pointer' }
const inp = { width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14 }
const lbl = { display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4, color: '#4a5568' }
