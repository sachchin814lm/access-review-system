import React, { useEffect, useState } from 'react'
import api from '../../api'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

const ROLES = ['employee', 'manager', 'app_owner', 'it_admin', 'auditor']
const ROLE_LABELS = { employee: 'Employee', manager: 'Manager', app_owner: 'App Owner', it_admin: 'IT Admin', auditor: 'Auditor' }

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [modal, setModal] = useState(null) // null | { type: 'create'|'edit', user? }
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const load = () => api.get('/users').then(r => setUsers(r.data.users))
  useEffect(load, [])

  const openCreate = () => { setModal({ type: 'create' }); setForm({ role: 'employee' }); setError('') }
  const openEdit = u => { setModal({ type: 'edit', user: u }); setForm({ ...u, password: '' }); setError('') }

  const handleSave = async () => {
    setSaving(true); setError('')
    try {
      if (modal.type === 'create') {
        await api.post('/users', form)
      } else {
        await api.put(`/users/${modal.user.id}`, form)
      }
      setModal(null); load()
    } catch (err) {
      setError(err.response?.data?.error || 'Save failed')
    } finally { setSaving(false) }
  }

  const handleDeactivate = async uid => {
    if (!window.confirm('Deactivate this user?')) return
    try { await api.delete(`/users/${uid}`); load() } catch {}
  }

  const managerOptions = users.filter(u => u.role === 'manager')

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0 }}>User Management</h2>
        <button onClick={openCreate} style={createBtn}>+ New User</button>
      </div>
      <div style={tableWrap}>
        <table style={tbl}>
          <thead><tr>
            <Th>Name</Th><Th>Username</Th><Th>Role</Th><Th>Manager</Th><Th>Status</Th><Th>Actions</Th>
          </tr></thead>
          <tbody>
            {users.map(u => {
              const mgr = users.find(m => m.id === u.manager_id)
              return (
                <tr key={u.id} style={{ borderBottom: '1px solid #e2e8f0', opacity: u.is_active ? 1 : 0.5 }}>
                  <Td><strong>{u.full_name}</strong></Td>
                  <Td>{u.username}</Td>
                  <Td>{ROLE_LABELS[u.role]}</Td>
                  <Td>{mgr?.full_name || '—'}</Td>
                  <Td><span style={{ color: u.is_active ? '#276749' : '#c53030', fontWeight: 600, fontSize: 13 }}>{u.is_active ? 'Active' : 'Inactive'}</span></Td>
                  <Td>
                    <button onClick={() => openEdit(u)} style={editBtn}>Edit</button>
                    {u.is_active && <button onClick={() => handleDeactivate(u.id)} style={delBtn}>Deactivate</button>}
                  </Td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal title={modal.type === 'create' ? '➕ New User' : '✏️ Edit User'} onClose={() => setModal(null)}>
          <ErrorBanner message={error} />
          {modal.type === 'create' && (
            <FormField label="Username *"><input style={inp} value={form.username || ''} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} /></FormField>
          )}
          <FormField label="Full Name *"><input style={inp} value={form.full_name || ''} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} /></FormField>
          <FormField label="Email *"><input style={inp} value={form.email || ''} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></FormField>
          {modal.type === 'create' && (
            <FormField label="Password *"><input type="password" style={inp} value={form.password || ''} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} /></FormField>
          )}
          <FormField label="Role *">
            <select style={inp} value={form.role || ''} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
              {ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
            </select>
          </FormField>
          <FormField label="Manager">
            <select style={inp} value={form.manager_id || ''} onChange={e => setForm(f => ({ ...f, manager_id: e.target.value ? Number(e.target.value) : null }))}>
              <option value="">— None —</option>
              {managerOptions.map(m => <option key={m.id} value={m.id}>{m.full_name}</option>)}
            </select>
          </FormField>
          {modal.type === 'edit' && (
            <FormField label="New Password (leave blank to keep)">
              <input type="password" style={inp} value={form.password || ''} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
            </FormField>
          )}
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

function FormField({ label, children }) {
  return <div style={{ marginBottom: 12 }}><label style={{ fontSize: 13, fontWeight: 600 }}>{label}</label><div style={{ marginTop: 4 }}>{children}</div></div>
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 600 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children }) => <td style={{ padding: '10px 14px', fontSize: 14 }}>{children}</td>
const createBtn = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }
const editBtn   = { padding: '4px 10px', background: '#ebf8ff', color: '#2b6cb0', border: 'none', borderRadius: 4, cursor: 'pointer', marginRight: 6, fontSize: 13 }
const delBtn    = { padding: '4px 10px', background: '#fff5f5', color: '#c53030', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13 }
const grayBtn   = { padding: '8px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 6, cursor: 'pointer' }
const inp = { width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14 }
