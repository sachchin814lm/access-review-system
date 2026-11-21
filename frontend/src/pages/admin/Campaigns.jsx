import React, { useEffect, useState } from 'react'
import api from '../../api'
import StatusBadge from '../../components/StatusBadge'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([])
  const [selected, setSelected] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [apps, setApps] = useState([])
  const [form, setForm] = useState({ name: '', description: '', scope: 'all', scope_ref_id: '', due_date: '' })
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  const load = () => api.get('/campaigns').then(r => setCampaigns(r.data.campaigns))
  useEffect(() => {
    load()
    api.get('/applications').then(r => setApps(r.data.applications))
  }, [])

  const loadDetail = async c => {
    const r = await api.get(`/campaigns/${c.id}`)
    setSelected(r.data.campaign)
  }

  const handleCreate = async () => {
    setError(''); setCreating(true)
    try {
      const payload = { name: form.name, description: form.description, scope: form.scope, due_date: form.due_date }
      if (form.scope === 'application') payload.scope_ref_id = Number(form.scope_ref_id)
      await api.post('/campaigns', payload)
      setShowCreate(false)
      setForm({ name: '', description: '', scope: 'all', scope_ref_id: '', due_date: '' })
      load()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create campaign')
    } finally { setCreating(false) }
  }

  const handleCancel = async cid => {
    if (!window.confirm('Cancel this campaign?')) return
    try { await api.post(`/campaigns/${cid}/cancel`); load() } catch {}
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0 }}>Review Campaigns</h2>
        <button onClick={() => setShowCreate(true)} style={createBtn}>+ New Campaign</button>
      </div>

      {!selected ? (
        <div style={tableWrap}>
          <table style={tbl}>
            <thead><tr>
              <Th>Name</Th><Th>Scope</Th><Th>Due Date</Th>
              <Th>Status</Th><Th>Progress</Th><Th>Actions</Th>
            </tr></thead>
            <tbody>
              {campaigns.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <Td><strong>{c.name}</strong></Td>
                  <Td>{c.scope}</Td>
                  <Td>{c.due_date}</Td>
                  <Td><StatusBadge status={c.status} /></Td>
                  <Td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={bar}>
                        <div style={{ ...fill, width: `${c.completion_pct}%` }} />
                      </div>
                      <span style={{ fontSize: 12 }}>{c.completion_pct}%</span>
                    </div>
                  </Td>
                  <Td>
                    <button onClick={() => loadDetail(c)} style={viewBtn}>View</button>
                    {c.status === 'Active' && (
                      <button onClick={() => handleCancel(c.id)} style={cancelBtn2}>Cancel</button>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <CampaignDetail campaign={selected} onBack={() => { setSelected(null); load() }} />
      )}

      {showCreate && (
        <Modal title="📅 New Review Campaign" onClose={() => setShowCreate(false)}>
          <ErrorBanner message={error} />
          {[
            { label: 'Campaign Name *', key: 'name', type: 'text' },
            { label: 'Description', key: 'description', type: 'text' },
            { label: 'Due Date *', key: 'due_date', type: 'date' },
          ].map(f => (
            <div key={f.key} style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>{f.label}</label>
              <input type={f.type} style={inp}
                value={form[f.key]} onChange={e => setForm(x => ({ ...x, [f.key]: e.target.value }))} />
            </div>
          ))}
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 600 }}>Scope *</label>
            <select style={inp} value={form.scope}
              onChange={e => setForm(x => ({ ...x, scope: e.target.value, scope_ref_id: '' }))}>
              <option value="all">All active grants</option>
              <option value="application">Specific application</option>
            </select>
          </div>
          {form.scope === 'application' && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>Application *</label>
              <select style={inp} value={form.scope_ref_id}
                onChange={e => setForm(x => ({ ...x, scope_ref_id: e.target.value }))}>
                <option value="">— Select —</option>
                {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
          )}
          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button onClick={handleCreate} disabled={creating} style={{ ...createBtn, flex: 1 }}>
              {creating ? '…' : 'Create Campaign'}
            </button>
            <button onClick={() => setShowCreate(false)} style={grayBtn}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function CampaignDetail({ campaign, onBack }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button onClick={onBack} style={grayBtn}>← Back</button>
        <h3 style={{ margin: 0 }}>{campaign.name}</h3>
        <StatusBadge status={campaign.status} />
      </div>
      <div style={{ display: 'flex', gap: 24, marginBottom: 16, fontSize: 14 }}>
        <span>Due: <strong>{campaign.due_date}</strong></span>
        <span>Progress: <strong>{campaign.completion_pct}%</strong> ({campaign.decided_items}/{campaign.total_items})</span>
        {campaign.overdue_items > 0 && <span style={{ color: '#c53030' }}>⚠ {campaign.overdue_items} overdue</span>}
      </div>
      <div style={tableWrap}>
        <table style={tbl}>
          <thead><tr>
            <Th>User</Th><Th>Application</Th><Th>Level</Th>
            <Th>Reviewer</Th><Th>Decision</Th><Th>Comments</Th>
          </tr></thead>
          <tbody>
            {(campaign.items || []).map(item => (
              <tr key={item.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <Td>{item.user_name}</Td>
                <Td>{item.application_name}</Td>
                <Td>{item.access_level}</Td>
                <Td>{item.reviewer_name}</Td>
                <Td><StatusBadge status={item.decision} /></Td>
                <Td style={{ fontSize: 13, color: '#718096' }}>{item.comments}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 600 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', fontSize: 14, ...style }}>{children}</td>
const bar = { flex: 1, height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }
const fill = { height: '100%', background: '#3182ce', borderRadius: 4 }
const createBtn  = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }
const viewBtn    = { padding: '5px 12px', background: '#ebf8ff', color: '#2b6cb0', border: 'none', borderRadius: 5, cursor: 'pointer', marginRight: 6 }
const cancelBtn2 = { padding: '5px 12px', background: '#fff5f5', color: '#c53030', border: 'none', borderRadius: 5, cursor: 'pointer' }
const grayBtn    = { padding: '8px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 6, cursor: 'pointer' }
const inp = { width: '100%', marginTop: 4, padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14 }
