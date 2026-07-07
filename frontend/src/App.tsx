import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './lib/auth';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import OwnerDashboard from './pages/OwnerDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';
import TenderDetailPage from './pages/TenderDetailPage';
import CreateTenderPage from './pages/CreateTenderPage';
import type { ReactNode } from 'react';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PublicRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/dashboard/owner" element={<ProtectedRoute><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/dashboard/manager" element={<ProtectedRoute><ManagerDashboard /></ProtectedRoute>} />
          <Route path="/dashboard/employee" element={<ProtectedRoute><EmployeeDashboard /></ProtectedRoute>} />
          <Route path="/tenders/new" element={<ProtectedRoute><CreateTenderPage /></ProtectedRoute>} />
          <Route path="/tenders/:tenderId" element={<ProtectedRoute><TenderDetailPage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
