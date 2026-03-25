import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiMenu, FiX, FiUser, FiLogOut } from 'react-icons/fi';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsMenuOpen(false);
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100">
      <div className="container mx-auto px-3 sm:px-4 md:px-6">
        <div className="flex justify-between items-center py-2.5 sm:py-3 md:py-4">
          {/* Elegant Logo */}
          <Link to="/" className="flex items-center space-x-2" onClick={closeMenu}>
            <img src="/logo.svg" alt="AuraFit" className="h-7 w-7 sm:h-8 sm:w-8 md:h-10 md:w-10" />
            <span className="text-base sm:text-lg md:text-xl font-bold text-gray-800 tracking-wide">AuraFit</span>
          </Link>

          {/* Mobile Menu Button */}
          <button
            onClick={toggleMenu}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>

          {/* Desktop Navigation Menu */}
          {isAuthenticated ? (
            <div className="hidden md:flex items-center space-x-4 lg:space-x-6">
              <Link to="/dashboard" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm lg:text-base tracking-wide uppercase">
                Dashboard
              </Link>
              <Link to="/recommendations" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm lg:text-base tracking-wide uppercase">
                Recommendations
              </Link>
              <Link to="/trends" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm lg:text-base tracking-wide uppercase">
                Trends
              </Link>
              <Link to="/profile" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm lg:text-base tracking-wide uppercase">
                Profile
              </Link>
              <div className="flex items-center space-x-3 lg:space-x-4 ml-4 lg:ml-6 pl-4 lg:pl-6 border-l border-gray-200">
                <span className="text-xs sm:text-sm text-gray-600 hidden lg:block">{user?.username}</span>
                <button
                  onClick={handleLogout}
                  className="bg-amber-600 text-white px-3 lg:px-5 py-1.5 sm:py-2 text-xs lg:text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors min-h-9"
                >
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="hidden md:flex items-center space-x-4 lg:space-x-6">
              <Link to="/login" className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm lg:text-base tracking-wide uppercase">
                Login
              </Link>
              <Link to="/register" className="bg-amber-600 text-white px-3 lg:px-5 py-1.5 sm:py-2 text-xs lg:text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors min-h-9">
                Start Now
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-100 py-3 sm:py-4 px-2">
            {isAuthenticated ? (
              <div className="flex flex-col space-y-2">
                <Link 
                  to="/dashboard" 
                  className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm tracking-wide uppercase px-2 py-2 rounded hover:bg-gray-50"
                  onClick={closeMenu}
                >
                  Dashboard
                </Link>
                <Link 
                  to="/recommendations" 
                  className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm tracking-wide uppercase px-2 py-2 rounded hover:bg-gray-50"
                  onClick={closeMenu}
                >
                  Recommendations
                </Link>
                <Link 
                  to="/trends" 
                  className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm tracking-wide uppercase px-2 py-2 rounded hover:bg-gray-50"
                  onClick={closeMenu}
                >
                  Trends
                </Link>
                <Link 
                  to="/profile" 
                  className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm tracking-wide uppercase px-2 py-2 rounded hover:bg-gray-50"
                  onClick={closeMenu}
                >
                  Profile
                </Link>
                <div className="border-t border-gray-200 pt-3 mt-2">
                  <div className="flex items-center px-2 py-2 mb-2">
                    <FiUser className="text-gray-500 mr-2" size={16} />
                    <span className="text-xs sm:text-sm text-gray-600">{user?.username}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full bg-amber-600 text-white px-3 py-2.5 sm:py-3 text-xs sm:text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors flex items-center justify-center space-x-2 rounded min-h-10"
                  >
                    <FiLogOut size={16} />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col space-y-2">
                <Link 
                  to="/login" 
                  className="text-gray-700 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm tracking-wide uppercase px-2 py-2 rounded hover:bg-gray-50"
                  onClick={closeMenu}
                >
                  Login
                </Link>
                <Link 
                  to="/register" 
                  className="bg-amber-600 text-white px-3 py-2.5 sm:py-3 text-xs sm:text-sm font-medium tracking-wide uppercase hover:bg-amber-700 transition-colors text-center rounded min-h-10 flex items-center justify-center"
                  onClick={closeMenu}
                >
                  Start Now
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
