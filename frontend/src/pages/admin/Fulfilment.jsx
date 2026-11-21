import React, { useEffect, useState } from 'react'
import api from '../../api'
import StatusBadge from '../../components/StatusBadge'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

export default function Fulfilment() {
  const [approved, setApproved] = useState([])
  const [grants, setGrants] = useState([])
  const [tab, setTab] = useState('grant') // 'grant' | 'revoke'
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // { type: 'grant'|'revoke', item }
  const [revokeReason, setRevokeReason] = useState('')
  const [error, setError] = useState('')
  const [acting, setActing] = useState(false)

  const loadAll = () => {
    setLoading(true)
    Promise.all([
      api.get('/fulfilment/approved').then(r => setApproved(r.data.requests)),
      api.get('/fulfilment', { params: { active_only: true } }).then(r => setGrants(r.data.grants)),
    ]).finally(() => setLoading(false))
  }
  useEffect(loadAll, [])

  const openGrant = req => { setModal({ type: 'grant', item: req }); setError('') }
  const openRevoke = grant => { setModal({ type: 'revoke', item: grant }); setRevokeReason(''); setError('') }

  const handleGrant = async () => {
    setActing(true); setError('')
    try {
      await api.post('/fulfilment', { request_id: modal.item.id })
      setModal(null); loadAll()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed')
    } finally { setActing(false) }
  }

  const handleRevoke = async () => {
    if (!revokeReason.trim()) return setError('Revoke reason is required')
    setActing(true); setError('')
    try {
      await api.patch(`/fulfilment/${modal.item.id}/revoke`, { revoke_reason: revokeReason })
      setModal(null); loadAll()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed')
    } finally { setActing(false) }
  }

  if (loading) return <p>Loading…</p>

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Fulfilment Panel</h2>
      <div style={tabs}>
        <button onClick={() => setTab('grant')} style={tab === 'grant' ? activeTab : inactiveTab}>
          ⚡ Grant Access ({approved.length})
        </button>
        <button onClick={() => setTab('revoke')} style={tab === 'revoke' ? activeTab : inactiveTab}>
          🗑 Active Grants ({grants.length})
        </button>
      </div>

      {tab === 'grant' && (
        <div style={tableWrap}>
          {approved.length === 0 ? (
            <EmptyState msg="No approved requests waiting to be granted." />
          ) : (
            <table style={tbl}>
              <thead><tr>
                <Th>#</Th><Th>Requester</Th><Th>Application</Th><Th>Level</Th><Th>Approved</Th><Th>Action</Th>
              </tr></thead>
              <tbody>
                {approved.map(r => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <Td>{r.id}</Td>
                    <Td><strong>{r.requester_name}</strong></Td>
                    <Td>{r.application_name}</Td>
                    <Td>{r.access_level}</Td>
                    <Td style={{ fontSize: 13, color: '#718096' }}>{new Date(r.updated_at).toLocaleDateString()}</Td>
                    <Td>
                      <button onClick={() => openGrant(r)} style={grantBtn}>Grant</button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'revoke' && (
        <div style={tableWrap}>
          {grants.length === 0 ? (
            <EmptyState msg="No active grants." />
          ) : (
            <table style={tbl}>
              <thead><tr>
                <Th>#</Th><Th>User</Th><Th>Application</Th><Th>Level</Th><Th>Granted</Th><Th>Action</Th>
              </tr></thead>
              <tbody>
                {grants.map(g => (
                  <tr key={g.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <Td>{g.id}</Td>
                    <Td><strong>{g.user_name}</strong></Td>
                    <Td>{g.application_name}</Td>
                    <Td>{g.access_level}</Td>
                    <Td style={{ fontSize: 13, color: '#718096' }}>{new Date(g.granted_at).toLocaleDateString()}</Td>
                    <Td>
                      <button onClick={() => openRevoke(g)} style={revokeBtn}>Revoke</button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {modal?.type === 'grant' && (
        <Modal title="⚡ Grant Access" onClose={() => setModal(null)}>
          <ErrorBanner message={error} />
          <p style={{ fontSize: 14, marginBottom: 16 }}>
            Grant <strong>{modal.item.access_level}</strong> access to <strong>{modal.item.application_name}</strong>
            {' '}for <strong>{modal.item.requester_name}</strong>?
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={handleGrant} disabled={acting} style={{ ...grantBtn, flex: 1, padding: 10 }}>
              {acting ? '…' : 'Confirm Grant'}
            </button>
            <button onClick={() => setModal(null)} style={cancelBtn}>Cancel</button>
          </div>
        </Modal>
      )}

      {modal?.type === 'revoke' && (
        <Modal title="🗑 Revoke Access" onClose={() => setModal(null)}>
          <ErrorBanner message={error} />
          <p style={{ fontSize: 14, marginBottom: 12 }}>
            Revoke <strong>{modal.item.access_level}</strong> for <strong>{modal.item.user_name}</strong>
            {' '}on <strong>{modal.item.application_name}</strong>?
          </p>
          <label style={{ fontSize: 13, fontWeight: 600 }}>Revoke Reason *</label>
          <textarea
            style={{ width: '100%', marginTop: 6, padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, minHeight: 70, fontSize: 14 }}
            value={revokeReason} onChange={e => setRevokeReason(e.target.value)}
            placeholder="Reason for revoking access…" />
          <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
            <button onClick={handleRevoke} disabled={acting} style={{ ...revokeBtn, flex: 1, padding: 10 }}>
              {acting ? '…' : 'Confirm Revoke'}
            </button>
            <button onClick={() => setModal(null)} style={cancelBtn}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function EmptyState({ msg }) {
  return <p style={{ padding: 24, color: '#718096', textAlign: 'center' }}>{msg}</p>
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)', marginTop: 16 }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 600 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', fontSize: 14, ...style }}>{children}</td>
const tabs = { display: 'flex', gap: 8, marginBottom: 0 }
const activeTab   = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: '6px 6px 0 0', cursor: 'pointer', fontWeight: 600 }
const inactiveTab = { padding: '8px 18px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: '6px 6px 0 0', cursor: 'pointer' }
const grantBtn   = { padding: '5px 14px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 13 }
const revokeBtn  = { padding: '5px 14px', background: '#c53030', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 13 }
const cancelBtn  = { padding: '5px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 5, cursor: 'pointer' }
