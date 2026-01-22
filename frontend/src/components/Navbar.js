import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100">
      <div className="container mx-auto px-6">
        <div className="flex justify-between items-center py-4">
          {/* Elegant Logo */}
          <Link to="/dashboard" className="flex items-center space-x-3">
            <img src="/logo.svg" alt="AuraFit" className="h-10 w-10" />
            <span className="text-xl font-bold text-gray-800 tracking-wide">AuraFit</span>
          </Link>

          {/* Navigation Menu */}
          {isAuthenticated ? (
            <div className="flex items-center space-x-8">
              <Link to="/dashboard" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-sm tracking-wide uppercase">
                Dashboard
              </Link>
              <Link to="/recommendations" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-sm tracking-wide uppercase">
                Recommendations
              </Link>
              <Link to="/trends" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-sm tracking-wide uppercase">
                Trends
              </Link>
              <Link to="/profile" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-sm tracking-wide uppercase">
                Profile
              </Link>
              <div className="flex items-center space-x-4 ml-8">
                <span className="text-sm text-gray-600">{user?.username}</span>
                <button
                  onClick={handleLogout}
                  className="bg-amber-600 text-white px-6 py-2 text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-8">
              <Link to="/login" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-sm tracking-wide uppercase">
                Login
              </Link>
              <Link to="/register" className="bg-amber-600 text-white px-6 py-2 text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors">
                Start Now
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
