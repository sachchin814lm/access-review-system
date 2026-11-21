import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = {
  employee: [
    { to: '/dashboard', label: '🏠 Dashboard' },
    { to: '/my-requests', label: '📋 My Requests' },
    { to: '/new-request', label: '➕ New Request' },
  ],
  manager: [
    { to: '/dashboard', label: '🏠 Dashboard' },
    { to: '/pending-approvals', label: '✅ Pending Approvals' },
    { to: '/review-items', label: '🔍 Review Items' },
  ],
  app_owner: [
    { to: '/dashboard', label: '🏠 Dashboard' },
    { to: '/pending-approvals', label: '✅ Pending Approvals' },
    { to: '/review-items', label: '🔍 Review Items' },
  ],
  it_admin: [
    { to: '/dashboard', label: '🏠 Dashboard' },
    { to: '/fulfilment', label: '⚡ Fulfilment' },
    { to: '/campaigns', label: '📅 Campaigns' },
    { to: '/admin/users', label: '👤 Users' },
    { to: '/admin/applications', label: '🗂 Applications' },
  ],
  auditor: [
    { to: '/dashboard', label: '🏠 Dashboard' },
    { to: '/audit-log', label: '📜 Audit Log' },
    { to: '/reports', label: '📊 Reports' },
  ],
}

const ROLE_LABEL = {
  employee: 'Employee', manager: 'Manager', app_owner: 'App Owner',
  it_admin: 'IT Admin', auditor: 'Auditor',
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const navItems = NAV[user?.role] || []

  return (
    <div style={wrap}>
      <aside style={sidebar}>
        <div style={logo}>
          <span style={{ fontSize: 22 }}>🔐</span>
          <span style={{ fontWeight: 700, fontSize: 15, marginLeft: 8, lineHeight: 1.2 }}>
            Access<br/>Review
          </span>
        </div>
        <nav style={{ flex: 1 }}>
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({ ...navLink, ...(isActive ? navActive : {}) })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div style={userBox}>
          <div style={{ fontSize: 12, color: '#a0aec0' }}>{ROLE_LABEL[user?.role]}</div>
          <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2 }}>{user?.full_name}</div>
          <button onClick={handleLogout} style={logoutBtn}>Logout</button>
        </div>
      </aside>
      <main style={main}>{children}</main>
    </div>
  )
}

const wrap = { display: 'flex', minHeight: '100vh' }
const sidebar = {
  width: 220, background: '#1a202c', color: '#e2e8f0',
  display: 'flex', flexDirection: 'column', flexShrink: 0,
  position: 'sticky', top: 0, height: '100vh',
}
const logo = {
  display: 'flex', alignItems: 'center', padding: '20px 20px 16px',
  borderBottom: '1px solid #2d3748',
}
const navLink = {
  display: 'block', padding: '10px 20px', color: '#a0aec0',
  textDecoration: 'none', fontSize: 14, transition: 'all 0.15s',
  borderLeft: '3px solid transparent',
}
const navActive = {
  color: '#fff', background: '#2d3748', borderLeftColor: '#4299e1',
}
const userBox = {
  padding: '14px 20px', borderTop: '1px solid #2d3748',
}
const logoutBtn = {
  marginTop: 8, padding: '5px 12px', background: '#e53e3e', color: '#fff',
  border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12,
}
const main = { flex: 1, padding: 24, maxWidth: 1100 }
