import React from 'react'

export default function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div style={{
      background: '#fff5f5', border: '1px solid #feb2b2', borderRadius: 6,
      padding: '10px 16px', color: '#c53030', marginBottom: 16, fontSize: 14,
    }}>
      ⚠ {message}
    </div>
  )
}
