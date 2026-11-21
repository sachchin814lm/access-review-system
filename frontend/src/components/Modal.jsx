import React, { useState } from 'react'

export default function Modal({ title, onClose, children }) {
  return (
    <div style={overlay}>
      <div style={box}>
        <div style={header}>
          <h3 style={{ margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={closeBtn}>✕</button>
        </div>
        <div style={{ padding: '20px 24px 24px' }}>{children}</div>
      </div>
    </div>
  )
}

const overlay = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
}
const box = {
  background: '#fff', borderRadius: 10, minWidth: 400, maxWidth: 560,
  width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
}
const header = {
  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  padding: '16px 24px', borderBottom: '1px solid #e2e8f0',
}
const closeBtn = {
  background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: '#718096'
}
