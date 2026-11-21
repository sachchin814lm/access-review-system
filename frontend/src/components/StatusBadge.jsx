import React from 'react'

const styles = {
  badge: {
    display: 'inline-block',
    padding: '2px 10px',
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.3,
  }
}

const colorMap = {
  'Pending Manager Approval': { bg: '#fefcbf', color: '#744210' },
  'Pending Owner Approval':   { bg: '#feebc8', color: '#7b341e' },
  'Approved':  { bg: '#c6f6d5', color: '#22543d' },
  'Granted':   { bg: '#bee3f8', color: '#2a4365' },
  'Rejected':  { bg: '#fed7d7', color: '#742a2a' },
  'Revoked':   { bg: '#e2e8f0', color: '#4a5568' },
  'Active':    { bg: '#c6f6d5', color: '#22543d' },
  'Completed': { bg: '#bee3f8', color: '#2a4365' },
  'Cancelled': { bg: '#e2e8f0', color: '#4a5568' },
  'Keep':      { bg: '#c6f6d5', color: '#22543d' },
  'Revoke':    { bg: '#fed7d7', color: '#742a2a' },
  'Pending':   { bg: '#fefcbf', color: '#744210' },
}

export default function StatusBadge({ status }) {
  const style = colorMap[status] || { bg: '#e2e8f0', color: '#4a5568' }
  return (
    <span style={{ ...styles.badge, background: style.bg, color: style.color }}>
      {status}
    </span>
  )
}
