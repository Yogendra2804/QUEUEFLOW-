import { Navigate } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { PageLoader } from './ui/Spinner';
import type { ReactNode } from 'react';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { manager, isLoading } = useAuth();
  if (isLoading) return <PageLoader />;
  if (!manager) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
