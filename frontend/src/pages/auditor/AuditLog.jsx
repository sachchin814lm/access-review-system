import React, { useEffect, useState } from 'react'
import api from '../../api'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [filters, setFilters] = useState({ action: '', entity_type: '', user_id: '' })
  const [loading, setLoading] = useState(false)

  const load = (p = 1) => {
    setLoading(true)
    const params = { page: p, per_page: 25 }
    if (filters.action) params.action = filters.action
    if (filters.entity_type) params.entity_type = filters.entity_type
    if (filters.user_id) params.user_id = filters.user_id
    api.get('/audit', { params })
      .then(r => { setLogs(r.data.logs); setTotal(r.data.total); setPages(r.data.pages); setPage(p) })
      .finally(() => setLoading(false))
  }

  useEffect(() => load(1), [])

  const handleSearch = e => { e.preventDefault(); load(1) }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Audit Log</h2>
      <form onSubmit={handleSearch} style={filterRow}>
        <input style={inp} placeholder="Filter by action…" value={filters.action}
          onChange={e => setFilters(f => ({ ...f, action: e.target.value }))} />
        <select style={inp} value={filters.entity_type}
          onChange={e => setFilters(f => ({ ...f, entity_type: e.target.value }))}>
          <option value="">All entity types</option>
          <option value="AccessRequest">AccessRequest</option>
          <option value="AccessGrant">AccessGrant</option>
          <option value="ReviewCampaign">ReviewCampaign</option>
          <option value="ReviewItem">ReviewItem</option>
        </select>
        <input style={inp} placeholder="User ID" value={filters.user_id}
          onChange={e => setFilters(f => ({ ...f, user_id: e.target.value }))} />
        <button type="submit" style={searchBtn}>Search</button>
      </form>

      <p style={{ color: '#718096', fontSize: 14, marginBottom: 8 }}>{total} total entries</p>

      <div style={tableWrap}>
        <table style={tbl}>
          <thead><tr>
            <Th>Timestamp</Th><Th>User</Th><Th>Action</Th>
            <Th>Entity</Th><Th>Details</Th>
          </tr></thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 24, color: '#718096' }}>Loading…</td></tr>
            ) : logs.map(log => (
              <tr key={log.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <Td style={{ fontSize: 12, color: '#718096', whiteSpace: 'nowrap' }}>
                  {new Date(log.timestamp).toLocaleString()}
                </Td>
                <Td>
                  <span style={{ fontWeight: 600 }}>{log.username}</span>
                  <div style={{ fontSize: 12, color: '#a0aec0' }}>{log.user_full_name}</div>
                </Td>
                <Td><code style={{ fontSize: 12, background: '#f7fafc', padding: '2px 6px', borderRadius: 4 }}>{log.action}</code></Td>
                <Td style={{ fontSize: 13 }}>{log.entity_type} #{log.entity_id}</Td>
                <Td style={{ fontSize: 12, color: '#718096', maxWidth: 200 }}>
                  {log.after_state && <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{JSON.stringify(log.after_state, null, 2).slice(0, 200)}</pre>}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div style={pagination}>
          <button onClick={() => load(page - 1)} disabled={page === 1} style={pageBtn}>← Prev</button>
          <span style={{ fontSize: 14 }}>Page {page} of {pages}</span>
          <button onClick={() => load(page + 1)} disabled={page === pages} style={pageBtn}>Next →</button>
        </div>
      )}
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 700 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children, style }) => <td style={{ padding: '10px 14px', verticalAlign: 'top', ...style }}>{children}</td>
const filterRow = { display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }
const inp = { padding: '8px 12px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14, minWidth: 160 }
const searchBtn = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }
const pagination = { display: 'flex', gap: 16, alignItems: 'center', marginTop: 16 }
const pageBtn = { padding: '6px 14px', background: '#e2e8f0', border: 'none', borderRadius: 5, cursor: 'pointer' }
