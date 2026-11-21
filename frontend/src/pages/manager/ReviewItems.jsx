import React, { useEffect, useState } from 'react'
import api from '../../api'
import StatusBadge from '../../components/StatusBadge'
import Modal from '../../components/Modal'
import ErrorBanner from '../../components/ErrorBanner'

export default function ReviewItems() {
  const [campaigns, setCampaigns] = useState([])
  const [selected, setSelected] = useState(null) // { campaign, items }
  const [modal, setModal] = useState(null) // { item, decision: 'Keep'|'Revoke' }
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [acting, setActing] = useState(false)

  useEffect(() => {
    api.get('/campaigns').then(r => setCampaigns(r.data.campaigns))
  }, [])

  const loadCampaign = campaign => {
    api.get(`/campaigns/${campaign.id}`).then(r => {
      const c = r.data.campaign
      setSelected({ campaign: c, items: c.items || [] })
    })
  }

  const openDecide = (item, decision) => {
    setModal({ item, decision }); setComment(''); setError('')
  }

  const handleDecide = async () => {
    setActing(true); setError('')
    try {
      await api.post(`/campaigns/${selected.campaign.id}/items/${modal.item.id}/decide`, {
        decision: modal.decision, comments: comment,
      })
      setModal(null)
      loadCampaign(selected.campaign)
    } catch (err) {
      setError(err.response?.data?.error || 'Action failed')
    } finally {
      setActing(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Review Items</h2>
      {!selected ? (
        <>
          <p style={{ color: '#718096', marginBottom: 16 }}>Select a campaign to review:</p>
          {campaigns.length === 0 ? (
            <p style={{ color: '#718096' }}>No active campaigns assigned to you.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 600 }}>
              {campaigns.map(c => (
                <div key={c.id} style={campaignCard}>
                  <div>
                    <strong>{c.name}</strong>
                    <span style={{ marginLeft: 12 }}><StatusBadge status={c.status} /></span>
                    <div style={{ fontSize: 13, color: '#718096', marginTop: 4 }}>
                      Due {c.due_date} · {c.completion_pct}% complete
                    </div>
                  </div>
                  {c.status === 'Active' && (
                    <button onClick={() => loadCampaign(c)} style={viewBtn}>View Items</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <button onClick={() => setSelected(null)} style={backBtn}>← Back</button>
            <h3 style={{ margin: 0 }}>{selected.campaign.name}</h3>
            <span>{selected.campaign.completion_pct}% complete</span>
          </div>
          <div style={tableWrap}>
            <table style={tbl}>
              <thead><tr>
                <Th>User</Th><Th>Application</Th><Th>Level</Th><Th>Decision</Th><Th>Actions</Th>
              </tr></thead>
              <tbody>
                {selected.items.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <Td>{item.user_name}</Td>
                    <Td>{item.application_name}</Td>
                    <Td>{item.access_level}</Td>
                    <Td><StatusBadge status={item.decision} /></Td>
                    <Td>
                      {item.decision === 'Pending' ? (
                        <>
                          <button onClick={() => openDecide(item, 'Keep')} style={keepBtn}>Keep</button>
                          <button onClick={() => openDecide(item, 'Revoke')} style={revokeBtn}>Revoke</button>
                        </>
                      ) : (
                        <span style={{ fontSize: 12, color: '#718096' }}>{item.comments}</span>
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {modal && (
        <Modal
          title={modal.decision === 'Keep' ? '✅ Keep Access' : '🗑 Revoke Access'}
          onClose={() => setModal(null)}
        >
          <ErrorBanner message={error} />
          <p style={{ fontSize: 14, marginBottom: 12 }}>
            <strong>{modal.item.user_name}</strong> → {modal.item.application_name} ({modal.item.access_level})
          </p>
          <label style={{ fontSize: 13, fontWeight: 600 }}>Comments (optional)</label>
          <textarea
            style={{ width: '100%', marginTop: 6, padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, minHeight: 70, fontSize: 14 }}
            value={comment} onChange={e => setComment(e.target.value)} />
          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button onClick={handleDecide} disabled={acting}
              style={{ ...(modal.decision === 'Keep' ? keepBtn : revokeBtn), flex: 1, padding: 10 }}>
              {acting ? '…' : `Confirm ${modal.decision}`}
            </button>
            <button onClick={() => setModal(null)} style={cancelBtn}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

const tableWrap = { background: '#fff', borderRadius: 10, overflow: 'auto', boxShadow: '0 1px 6px rgba(0,0,0,0.07)' }
const tbl = { width: '100%', borderCollapse: 'collapse' }
const Th = ({ children }) => <th style={{ textAlign: 'left', fontSize: 12, padding: '10px 14px', color: '#718096', background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>{children}</th>
const Td = ({ children }) => <td style={{ padding: '10px 14px', fontSize: 14 }}>{children}</td>
const campaignCard = { background: '#fff', borderRadius: 8, padding: '14px 18px', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }
const viewBtn = { padding: '6px 14px', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer' }
const backBtn = { padding: '5px 12px', background: '#e2e8f0', border: 'none', borderRadius: 5, cursor: 'pointer' }
const keepBtn   = { padding: '5px 12px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', marginRight: 6, fontSize: 13 }
const revokeBtn = { padding: '5px 12px', background: '#c53030', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 13 }
const cancelBtn = { padding: '5px 16px', background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 5, cursor: 'pointer' }
