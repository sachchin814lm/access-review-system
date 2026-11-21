import React, { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api'
import StatusBadge from '../components/StatusBadge'

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState({})

  useEffect(() => {
    if (!user) return
    const fetches = []
    if (user.role === 'employee' || user.role === 'manager' || user.role === 'app_owner') {
      fetches.push(api.get('/requests/mine').then(r => setData(d => ({ ...d, myRequests: r.data.requests }))))
    }
    if (user.role === 'manager' || user.role === 'app_owner') {
      fetches.push(api.get('/requests/pending').then(r => setData(d => ({ ...d, pending: r.data.requests }))))
    }
    if (user.role === 'it_admin') {
      fetches.push(api.get('/fulfilment/approved').then(r => setData(d => ({ ...d, approved: r.data.requests }))))
      fetches.push(api.get('/campaigns').then(r => setData(d => ({ ...d, campaigns: r.data.campaigns }))))
    }
    if (user.role === 'auditor') {
      fetches.push(api.get('/audit', { params: { per_page: 5 } }).then(r => setData(d => ({ ...d, recentLogs: r.data.logs }))))
    }
    Promise.all(fetches)
  }, [user])

  const cards = getCards(user?.role, data)

  return (
    <div>
      <h2 style={{ marginBottom: 4 }}>Dashboard</h2>
      <p style={{ color: '#718096', marginBottom: 24 }}>
        Welcome, <strong>{user?.full_name}</strong> · {ROLE_LABELS[user?.role]}
      </p>
      <div style={grid}>
        {cards.map((c, i) => (
          <div key={i} style={{ ...statCard, borderTopColor: c.color }}>
            <div style={{ fontSize: 32 }}>{c.icon}</div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{c.value}</div>
            <div style={{ fontSize: 14, color: '#718096' }}>{c.label}</div>
          </div>
        ))}
      </div>
      {user?.role === 'auditor' && data.recentLogs && (
        <div style={section}>
          <h3 style={{ marginBottom: 12 }}>Recent Audit Activity</h3>
          <table style={tbl}>
            <thead><tr>
              <Th>Time</Th><Th>User</Th><Th>Action</Th><Th>Entity</Th>
            </tr></thead>
            <tbody>
              {data.recentLogs.map(log => (
                <tr key={log.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <Td>{new Date(log.timestamp).toLocaleString()}</Td>
                  <Td>{log.username}</Td>
                  <Td><code style={{ fontSize: 12 }}>{log.action}</code></Td>
                  <Td>{log.entity_type} #{log.entity_id}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {user?.role === 'it_admin' && data.campaigns && (
        <div style={section}>
          <h3 style={{ marginBottom: 12 }}>Active Campaigns</h3>
          {data.campaigns.filter(c => c.status === 'Active').map(c => (
            <div key={c.id} style={campaignRow}>
              <div>
                <strong>{c.name}</strong>
                <span style={{ marginLeft: 12, color: '#718096', fontSize: 13 }}>
                  Due {c.due_date}
                </span>
              </div>
              <div style={{ fontSize: 14 }}>
                <strong>{c.completion_pct}%</strong> complete
                ({c.decided_items}/{c.total_items} items)
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function getCards(role, data) {
  if (role === 'employee') return [
    { icon: '📋', value: data.myRequests?.length ?? '…', label: 'My Requests', color: '#3182ce' },
    { icon: '⏳', value: data.myRequests?.filter(r => r.status.startsWith('Pending')).length ?? '…', label: 'Pending', color: '#d69e2e' },
    { icon: '✅', value: data.myRequests?.filter(r => r.status === 'Granted').length ?? '…', label: 'Granted', color: '#38a169' },
  ]
  if (role === 'manager' || role === 'app_owner') return [
    { icon: '✅', value: data.pending?.length ?? '…', label: 'Pending Approvals', color: '#d69e2e' },
    { icon: '📋', value: data.myRequests?.length ?? '…', label: 'My Requests', color: '#3182ce' },
  ]
  if (role === 'it_admin') return [
    { icon: '⚡', value: data.approved?.length ?? '…', label: 'Ready to Grant', color: '#38a169' },
    { icon: '📅', value: data.campaigns?.filter(c => c.status === 'Active').length ?? '…', label: 'Active Campaigns', color: '#3182ce' },
    { icon: '🔄', value: data.campaigns?.reduce((s, c) => s + (c.total_items - c.decided_items), 0) ?? '…', label: 'Pending Review Items', color: '#d69e2e' },
  ]
  if (role === 'auditor') return [
    { icon: '📜', value: data.recentLogs?.length ?? '…', label: 'Recent Log Entries', color: '#805ad5' },
  ]
  return []
}

const ROLE_LABELS = {
  employee: 'Employee', manager: 'Manager', app_owner: 'Application Owner',
  it_admin: 'IT Administrator', auditor: 'Auditor',
}
const grid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px,1fr))', gap: 16, marginBottom: 32 }
const statCard = {
  background: '#fff', borderRadius: 10, padding: '20px', borderTop: '4px solid #3182ce',
  boxShadow: '0 1px 6px rgba(0,0,0,0.07)', display: 'flex', flexDirection: 'column', gap: 4,
}
const section = { background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 6px rgba(0,0,0,0.07)', marginBottom: 24 }
const tbl = { width: '100%', borderCollapse: 'collapse' }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '6px 10px', color: '#718096', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children }) => <td style={{ padding: '8px 10px', fontSize: 14 }}>{children}</td>
const campaignRow = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  padding: '10px 0', borderBottom: '1px solid #e2e8f0',
}
