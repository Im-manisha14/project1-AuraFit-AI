import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiArrowRight, FiShoppingBag, FiTrendingUp, FiUser } from 'react-icons/fi';

const Landing = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
      {/* Hero Section */}
      <div className="container mx-auto px-3 sm:px-4 md:px-6 py-12 sm:py-16 md:py-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 sm:mb-6 tracking-tight">
            Welcome to <span className="text-purple-600">AuraFit</span>
          </h1>
          <p className="text-base sm:text-xl text-gray-600 mb-8 sm:mb-12 font-light leading-relaxed px-2">
            Your AI-Powered Personal Fashion Stylist
          </p>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-6 justify-center mb-12 sm:mb-20 px-2">
            <Link
              to="/register"
              className="group bg-purple-600 text-white px-6 sm:px-10 py-3 sm:py-4 text-base sm:text-lg font-medium tracking-wide uppercase hover:bg-purple-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center space-x-2 sm:space-x-3 min-h-11 sm:min-h-14"
            >
              <span>Get Started</span>
              <FiArrowRight className="group-hover:translate-x-2 transition-transform" />
            </Link>
            <Link
              to="/login"
              className="bg-white text-purple-600 px-6 sm:px-10 py-3 sm:py-4 text-base sm:text-lg font-medium tracking-wide uppercase hover:bg-gray-50 transition-all shadow-lg hover:shadow-xl border-2 border-purple-600 min-h-11 sm:min-h-14 flex items-center justify-center"
            >
              Sign In
            </Link>
          </div>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 md:gap-8 max-w-5xl mx-auto"
        >
          <div className="bg-white p-5 sm:p-6 md:p-8 rounded-lg shadow-md text-center">
            <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <FiUser className="text-xl sm:text-2xl md:text-3xl text-purple-600" />
            </div>
            <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-2 sm:mb-3">
              AI Skin Tone Analysis
            </h3>
            <p className="text-gray-600 text-xs sm:text-sm md:text-base">
              Advanced hand detection technology analyzes your skin tone for personalized color recommendations.
            </p>
          </div>

          <div className="bg-white p-5 sm:p-6 md:p-8 rounded-lg shadow-md text-center">
            <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <FiShoppingBag className="text-xl sm:text-2xl md:text-3xl text-blue-600" />
            </div>
            <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-2 sm:mb-3">
              Smart Outfit Recommendations
            </h3>
            <p className="text-gray-600 text-xs sm:text-sm md:text-base">
              Get AI-powered outfit suggestions based on your body type, preferences, and style.
            </p>
          </div>

          <div className="bg-white p-5 sm:p-6 md:p-8 rounded-lg shadow-md text-center">
            <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <FiTrendingUp className="text-xl sm:text-2xl md:text-3xl text-pink-600" />
            </div>
            <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-2 sm:mb-3">
              Fashion Trends
            </h3>
            <p className="text-gray-600 text-xs sm:text-sm md:text-base">
              Stay updated with the latest fashion trends and discover what's hot in the fashion world.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Landing;
