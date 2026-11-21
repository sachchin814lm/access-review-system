import React, { useEffect, useState } from 'react'
import api from '../../api'
import StatusBadge from '../../components/StatusBadge'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

export default function PendingApprovals() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // { req, type: 'approve'|'reject' }
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [acting, setActing] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/requests/pending')
      .then(r => setRequests(r.data.requests))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const openModal = (req, type) => { setModal({ req, type }); setComment(''); setError('') }
  const closeModal = () => setModal(null)

  const handleDecide = async () => {
    setActing(true)
    setError('')
    try {
      const endpoint = modal.type === 'approve'
        ? `/requests/${modal.req.id}/approve`
        : `/requests/${modal.req.id}/reject`
      await api.post(endpoint, { comments: comment })
      closeModal()
      load()
    } catch (err) {
      setError(err.response?.data?.error || 'Action failed')
    } finally {
      setActing(false)
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Pending Approvals</h2>
      {requests.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={tableWrap}>
          <table style={tbl}>
            <thead><tr>
              <Th>#</Th><Th>Requester</Th><Th>Application</Th>
              <Th>Level</Th><Th>Justification</Th><Th>Status</Th><Th>Actions</Th>
            </tr></thead>
            <tbody>
              {requests.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <Td>{r.id}</Td>
                  <Td><strong>{r.requester_name}</strong></Td>
                  <Td>{r.application_name}</Td>
                  <Td>{r.access_level}</Td>
                  <Td style={{ maxWidth: 220, fontSize: 13, color: '#4a5568' }}>{r.justification}</Td>
                  <Td><StatusBadge status={r.status} /></Td>
                  <Td>
                    <button onClick={() => openModal(r, 'approve')} style={approveBtn}>Approve</button>
                    <button onClick={() => openModal(r, 'reject')} style={rejectBtn}>Reject</button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <Modal
          title={modal.type === 'approve' ? '✅ Approve Request' : '❌ Reject Request'}
          onClose={closeModal}
        >
          <ErrorBanner message={error} />
          <p style={{ marginBottom: 12, fontSize: 14 }}>
            <strong>{modal.req.requester_name}</strong> → {modal.req.application_name} ({modal.req.access_level})
          </p>
          <label style={{ fontSize: 13, fontWeight: 600 }}>Comments (optional)</label>
          <textarea
            style={{ width: '100%', marginTop: 6, padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, minHeight: 80, resize: 'vertical', fontSize: 14 }}
            value={comment} onChange={e => setComment(e.target.value)}
            placeholder="Add a comment…"
          />
          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button onClick={handleDecide} disabled={acting}
              style={{ ...(modal.type === 'approve' ? approveBtn : rejectBtn), flex: 1, padding: 10 }}>
              {acting ? '…' : modal.type === 'approve' ? 'Confirm Approve' : 'Confirm Reject'}
            </button>
            <button onClick={closeModal} style={cancelBtn}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', padding: '48px 0', color: '#718096' }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>🎉</div>
      <p>No pending approvals — you're all caught up!</p>
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 700 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', fontSize: 14, ...style }}>{children}</td>
const approveBtn = { padding: '5px 12px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', marginRight: 6, fontSize: 13 }
const rejectBtn  = { padding: '5px 12px', background: '#c53030', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 13 }
const cancelBtn  = { padding: '5px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 5, cursor: 'pointer' }
