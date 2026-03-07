import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userAPI } from '../services/api';
import { motion } from 'framer-motion';
import { FiMail, FiLock, FiArrowRight } from 'react-icons/fi';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, user } = useAuth();
  const navigate = useNavigate();

  // If already logged in, check profile and redirect appropriately
  useEffect(() => {
    if (user) {
      userAPI.getProfile()
        .then(res => {
          const p = res.data.profile;
          const done = p && p.body_type && p.age && p.gender;
          navigate(done ? '/recommendations' : '/profile', { replace: true });
        })
        .catch(() => navigate('/profile', { replace: true }));
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);

      if (result.success) {
        // Check profile completeness — skip profile page if already filled
        try {
          const res = await userAPI.getProfile();
          const p = res.data.profile;
          const done = p && p.body_type && p.age && p.gender;
          navigate(done ? '/recommendations' : '/profile', { replace: true });
        } catch {
          navigate('/profile', { replace: true });
        }
      } else {
        setError(result.error);
        setLoading(false);
      }
    } catch (err) {
      setError('An unexpected error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-3 sm:px-4 py-6 sm:py-12">
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-md w-full"
      >
        <div className="bg-white border border-gray-200 p-6 sm:p-10 shadow-sm">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-center mb-6 sm:mb-10"
          >
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 sm:mb-3 tracking-tight">
              Welcome Back
            </h1>
            <p className="text-gray-600 font-light text-sm sm:text-base">Sign in to your luxury fashion experience</p>
          </motion.div>

          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-red-50 border border-red-200 text-red-800 px-3 sm:px-4 py-2 sm:py-3 mb-4 sm:mb-6 text-xs sm:text-sm"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <label className="block text-gray-900 font-medium mb-2 sm:mb-3 text-xs sm:text-sm tracking-wide uppercase flex items-center space-x-1 sm:space-x-2">
                <FiMail className="text-amber-600 text-sm sm:text-base" />
                <span>Email Address</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 sm:px-4 py-3 sm:py-4 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900 text-sm sm:text-base"
                placeholder="your.email@example.com"
                required
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              <label className="block text-gray-900 font-medium mb-2 sm:mb-3 text-xs sm:text-sm tracking-wide uppercase flex items-center space-x-1 sm:space-x-2">
                <FiLock className="text-amber-600 text-sm sm:text-base" />
                <span>Password</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 sm:px-4 py-3 sm:py-4 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900 text-sm sm:text-base"
                placeholder="••••••••••"
                required
              />
            </motion.div>

            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="group w-full bg-gray-900 text-white py-3 sm:py-4 font-medium text-xs sm:text-sm tracking-widest uppercase hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
              disabled={loading}
            >
              <span>{loading ? 'Signing In...' : 'Sign In'}</span>
              {!loading && <FiArrowRight className="group-hover:translate-x-1 transition-transform text-sm sm:text-base" />}
            </motion.button>
          </form>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="mt-6 sm:mt-8 text-center"
          >
            <p className="text-gray-600 font-light text-sm sm:text-base">
              Don't have an account?{' '}
              <Link to="/register" className="text-amber-600 font-medium hover:text-amber-700 transition-colors">
                Create Account
              </Link>
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
