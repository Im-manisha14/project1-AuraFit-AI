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
    <nav className="gradient-bg text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <Link to="/dashboard" className="flex items-center space-x-2">
            <span className="text-2xl font-bold">✨ StyleSync</span>
          </Link>

          {isAuthenticated && (
            <div className="flex items-center space-x-6">
              <Link to="/dashboard" className="hover:text-purple-200 transition">
                Dashboard
              </Link>
              <Link to="/recommendations" className="hover:text-purple-200 transition">
                Recommendations
              </Link>
              <Link to="/trends" className="hover:text-purple-200 transition">
                Trends
              </Link>
              <Link to="/profile" className="hover:text-purple-200 transition">
                Profile
              </Link>
              <div className="flex items-center space-x-4">
                <span className="text-sm">👤 {user?.username}</span>
                <button
                  onClick={handleLogout}
                  className="bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-purple-100 transition"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
