import React, { useEffect, useState } from 'react'
import api from '../../api'

const REPORTS = [
  { id: 'access-by-user',       label: '👤 Access by User',       desc: 'All currently granted accesses grouped by user' },
  { id: 'access-by-application',label: '🗂 Access by Application', desc: 'All currently granted accesses by application' },
  { id: 'pending-approvals',    label: '⏳ Pending Approvals',     desc: 'Requests awaiting approval' },
  { id: 'overdue-reviews',      label: '⚠ Overdue Reviews',       desc: 'Review items past due date' },
  { id: 'revoked-access',       label: '🗑 Revoked Access',        desc: 'All revoked grants with reasons' },
  { id: 'campaign-results',     label: '📅 Campaign Results',      desc: 'Detailed campaign result by campaign ID', needsId: true },
]

export default function Reports() {
  const [selected, setSelected] = useState(null)
  const [data, setData] = useState(null)
  const [campaignId, setCampaignId] = useState('')
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/campaigns').then(r => setCampaigns(r.data.campaigns)).catch(() => {})
  }, [])

  const runReport = async () => {
    setLoading(true); setError(''); setData(null)
    try {
      const params = {}
      if (selected.needsId) {
        if (!campaignId) { setError('Please select a campaign'); setLoading(false); return }
        params.campaign_id = campaignId
      }
      const r = await api.get(`/reports/${selected.id}`, { params })
      setData(r.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Report failed')
    } finally { setLoading(false) }
  }

  const downloadCSV = async () => {
    const params = { format: 'csv' }
    if (selected.needsId) params.campaign_id = campaignId
    const r = await api.get(`/reports/${selected.id}`, { params, responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([r.data]))
    const a = document.createElement('a'); a.href = url
    a.download = `${selected.id}.csv`; a.click()
    URL.revokeObjectURL(url)
  }

  const rows = data?.rows || []
  const cols = rows.length > 0 ? Object.keys(rows[0]) : []

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Reports</h2>
      <div style={reportGrid}>
        {REPORTS.map(r => (
          <div key={r.id}
            onClick={() => { setSelected(r); setData(null); setError('') }}
            style={{ ...reportCard, ...(selected?.id === r.id ? selectedCard : {}) }}
          >
            <div style={{ fontWeight: 600 }}>{r.label}</div>
            <div style={{ fontSize: 12, color: '#718096', marginTop: 4 }}>{r.desc}</div>
          </div>
        ))}
      </div>

      {selected && (
        <div style={panel}>
          <h3 style={{ marginBottom: 12 }}>{selected.label}</h3>
          {selected.needsId && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>Select Campaign</label>
              <select style={inp} value={campaignId} onChange={e => setCampaignId(e.target.value)}>
                <option value="">— Select —</option>
                {campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          )}
          {error && <div style={{ color: '#c53030', marginBottom: 10, fontSize: 14 }}>⚠ {error}</div>}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button onClick={runReport} disabled={loading} style={runBtn}>
              {loading ? 'Loading…' : 'Run Report'}
            </button>
            {data && rows.length > 0 && (
              <button onClick={downloadCSV} style={csvBtn}>⬇ Download CSV</button>
            )}
          </div>

          {data && (
            <>
              {data.summary && (
                <div style={summaryRow}>
                  {Object.entries(data.summary).map(([k, v]) => (
                    <div key={k} style={summaryItem}><strong>{v}</strong><div style={{ fontSize: 12, color: '#718096' }}>{k}</div></div>
                  ))}
                </div>
              )}
              {rows.length === 0 ? (
                <p style={{ color: '#718096', textAlign: 'center', padding: 24 }}>No data for this report.</p>
              ) : (
                <div style={tableWrap}>
                  <table style={tbl}>
                    <thead><tr>{cols.map(c => <Th key={c}>{c}</Th>)}</tr></thead>
                    <tbody>
                      {rows.map((row, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid #e2e8f0' }}>
                          {cols.map(c => <Td key={c}>{String(row[c] ?? '')}</Td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p style={{ fontSize: 12, color: '#a0aec0', marginTop: 8 }}>
                Showing {rows.length} row(s)
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

const reportGrid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))', gap: 12, marginBottom: 20 }
const reportCard = { background: '#fff', borderRadius: 8, padding: '14px 16px', cursor: 'pointer', border: '2px solid transparent', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', transition: 'all 0.15s' }
const selectedCard = { borderColor: '#3182ce', background: '#ebf8ff' }
const panel = { background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tableWrap = { overflow: 'auto' }
const tbl = { width: '100%', borderCollapse: 'collapse', minWidth: 500 }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '8px 12px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }}>{children}</th>
const Td = ({ children }) => <td style={{ padding: '8px 12px', fontSize: 13 }}>{children}</td>
const inp = { display: 'block', marginTop: 4, padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 14, minWidth: 220 }
const runBtn = { padding: '8px 18px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }
const csvBtn = { padding: '8px 18px', background: '#276749', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }
const summaryRow = { display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }
const summaryItem = { background: '#f7fafc', borderRadius: 8, padding: '10px 18px', textAlign: 'center', fontSize: 20 }
