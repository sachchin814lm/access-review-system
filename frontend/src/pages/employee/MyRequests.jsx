import React, { useEffect, useState } from 'react'
import api from '../../api'
import StatusBadge from '../../components/StatusBadge'

export default function MyRequests() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/requests/mine')
      .then(r => setRequests(r.data.requests))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading…</p>

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>My Access Requests</h2>
      {requests.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={tableWrap}>
          <table style={tbl}>
            <thead>
              <tr>
                <Th>#</Th><Th>Application</Th><Th>Level</Th>
                <Th>Status</Th><Th>Submitted</Th><Th>Approvals</Th>
              </tr>
            </thead>
            <tbody>
              {requests.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <Td>{r.id}</Td>
                  <Td><strong>{r.application_name}</strong></Td>
                  <Td>{r.access_level}</Td>
                  <Td><StatusBadge status={r.status} /></Td>
                  <Td style={{ color: '#718096', fontSize: 13 }}>{new Date(r.created_at).toLocaleDateString()}</Td>
                  <Td>
                    {(r.approvals || []).map(a => (
                      <div key={a.id} style={{ fontSize: 12, color: a.decision === 'approved' ? '#276749' : '#c53030' }}>
                        {a.approval_type}: {a.decision}
                        {a.comments && <span style={{ color: '#718096' }}> — {a.comments}</span>}
                      </div>
                    ))}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', padding: '48px 0', color: '#718096' }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
      <p>You haven't submitted any access requests yet.</p>
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse' }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', fontSize: 14, ...style }}>{children}</td>
