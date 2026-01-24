import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();
  const hasToken = !!localStorage.getItem('access_token');

  console.log('[PrivateRoute]', {
    loading,
    isAuthenticated,
    hasUser: !!user,
    hasToken,
    path: location.pathname,
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-amber-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Loading AuraFit...</p>
        </div>
      </div>
    );
  }

  // Allow access if user has a token, even if checkAuth hasn't completed yet
  // This prevents the race condition where tokens exist but user state hasn't loaded
  if (!isAuthenticated && !hasToken) {
    console.warn('[PrivateRoute] Not authenticated - redirecting to login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default PrivateRoute;
