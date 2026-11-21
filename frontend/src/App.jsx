import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewRequest from './pages/employee/NewRequest'
import MyRequests from './pages/employee/MyRequests'
import PendingApprovals from './pages/manager/PendingApprovals'
import ReviewItems from './pages/manager/ReviewItems'
import Fulfilment from './pages/admin/Fulfilment'
import Campaigns from './pages/admin/Campaigns'
import UserManagement from './pages/admin/UserManagement'
import AppManagement from './pages/admin/AppManagement'
import AuditLog from './pages/auditor/AuditLog'
import Reports from './pages/auditor/Reports'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={
        <ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>
      } />
      <Route path="/my-requests" element={
        <ProtectedRoute><Layout><MyRequests /></Layout></ProtectedRoute>
      } />
      <Route path="/new-request" element={
        <ProtectedRoute roles={['employee', 'manager', 'app_owner']}><Layout><NewRequest /></Layout></ProtectedRoute>
      } />
      <Route path="/pending-approvals" element={
        <ProtectedRoute roles={['manager', 'app_owner']}><Layout><PendingApprovals /></Layout></ProtectedRoute>
      } />
      <Route path="/review-items" element={
        <ProtectedRoute roles={['manager', 'app_owner']}><Layout><ReviewItems /></Layout></ProtectedRoute>
      } />
      <Route path="/fulfilment" element={
        <ProtectedRoute roles={['it_admin']}><Layout><Fulfilment /></Layout></ProtectedRoute>
      } />
      <Route path="/campaigns" element={
        <ProtectedRoute roles={['it_admin']}><Layout><Campaigns /></Layout></ProtectedRoute>
      } />
      <Route path="/admin/users" element={
        <ProtectedRoute roles={['it_admin']}><Layout><UserManagement /></Layout></ProtectedRoute>
      } />
      <Route path="/admin/applications" element={
        <ProtectedRoute roles={['it_admin']}><Layout><AppManagement /></Layout></ProtectedRoute>
      } />
      <Route path="/audit-log" element={
        <ProtectedRoute roles={['auditor', 'it_admin']}><Layout><AuditLog /></Layout></ProtectedRoute>
      } />
      <Route path="/reports" element={
        <ProtectedRoute roles={['auditor', 'it_admin']}><Layout><Reports /></Layout></ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
