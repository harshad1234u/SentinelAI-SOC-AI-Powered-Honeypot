import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Layout } from '../components/Layout';
import { ErrorBoundary } from '../components/ErrorBoundary';

// Lazy load pages for code splitting
const Login = lazy(() => import('../pages/Login'));
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Feed = lazy(() => import('../pages/Feed'));
const Investigation = lazy(() => import('../pages/Investigation'));
const Assistant = lazy(() => import('../pages/Assistant'));
const Alerts = lazy(() => import('../pages/Alerts'));
const Settings = lazy(() => import('../pages/Settings'));

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center w-full h-full min-h-[400px]">
    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="h-screen w-screen bg-background flex items-center justify-center"><PageLoader /></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={
          <Suspense fallback={<div className="h-screen w-screen bg-background flex items-center justify-center"><PageLoader /></div>}>
            <Login />
          </Suspense>
        } />
        
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={
            <Suspense fallback={<PageLoader />}>
              <Dashboard />
            </Suspense>
          } />
          <Route path="feed" element={
            <Suspense fallback={<PageLoader />}>
              <Feed />
            </Suspense>
          } />
          <Route path="attacks/:id" element={
            <Suspense fallback={<PageLoader />}>
              <Investigation />
            </Suspense>
          } />
          <Route path="assistant" element={
            <Suspense fallback={<PageLoader />}>
              <Assistant />
            </Suspense>
          } />
          <Route path="alerts" element={
            <Suspense fallback={<PageLoader />}>
              <Alerts />
            </Suspense>
          } />
          <Route path="settings" element={
            <Suspense fallback={<PageLoader />}>
              <Settings />
            </Suspense>
          } />
        </Route>
        
        {/* Catch all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ErrorBoundary>
  );
};
