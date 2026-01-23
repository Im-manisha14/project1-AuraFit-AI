import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationAPI, userAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { FiStar, FiTrendingUp, FiCalendar, FiAward, FiHeart, FiUser, FiArrowRight } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

const Recommendations = () => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileComplete, setProfileComplete] = useState(true);
  const [filters, setFilters] = useState({
    occasion: 'casual',
    season: 'all',
    limit: 10,
  });

  useEffect(() => {
    checkProfileStatus();
  }, []);

  const checkProfileStatus = async () => {
    try {
      const profileRes = await userAPI.getProfile();
      const prefsRes = await userAPI.getPreferences();
      
      const profile = profileRes.data.profile;
      const prefs = prefsRes.data.preferences;
      
      // Check if essential profile fields are filled
      const isComplete = profile?.body_type && profile?.age && profile?.gender && 
                        prefs?.preferred_styles?.length > 0;
      
      setProfileComplete(isComplete);
    } catch (error) {
      // Don't fail - just assume profile needs completion
      console.error('Error checking profile:', error);
      setProfileComplete(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const generateRecommendations = async () => {
    if (!profileComplete) {
      setShowProfileModal(true);
      return;
    }

    setLoading(true);
    try {
      const response = await recommendationAPI.generate(filters);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error generating recommendations:', error);
      setShowProfileModal(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGoToProfile = () => {
    navigate('/profile');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section with Luxury Fashion Background */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="relative text-white overflow-hidden"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2070)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        {/* Elegant overlay with gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/70 to-black/60"></div>
        
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-10 right-10 w-64 h-64 bg-amber-600 opacity-10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-10 left-10 w-96 h-96 bg-amber-500 opacity-5 rounded-full blur-3xl"></div>
        </div>
        
        {/* Luxury pattern overlay */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.03) 35px, rgba(255,255,255,.03) 70px)'
        }}></div>
        
        <div className="relative z-10 container mx-auto px-6 py-24">
          <motion.div
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-center max-w-3xl mx-auto"
          >
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="inline-block mb-6"
            >
              <HiOutlineSparkles className="text-6xl text-amber-500 mx-auto drop-shadow-lg" />
            </motion.div>
            <motion.h1 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-6xl font-bold mb-6 tracking-tight drop-shadow-lg"
            >
              Personalized Recommendations
            </motion.h1>
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="relative"
            >
              <div className="w-20 h-1 bg-amber-600 mx-auto mb-6"></div>
              <p className="text-xl text-gray-200 font-light leading-relaxed drop-shadow-md">
                Discover curated outfits tailored exclusively for your style, body type, and preferences
              </p>
            </motion.div>
          </motion.div>
        </div>
      </motion.div>

      {/* Filters Section */}
      <div className="container mx-auto px-6 py-12">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="bg-white border border-gray-200 p-8 shadow-sm mb-12"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6 tracking-tight">Customize Your Recommendations</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div>
              <label className="block text-gray-900 font-medium mb-3 text-sm tracking-wide uppercase flex items-center space-x-2">
                <FiCalendar className="text-amber-600" />
                <span>Occasion</span>
              </label>
              <select
                name="occasion"
                value={filters.occasion}
                onChange={handleFilterChange}
                className="w-full px-4 py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900"
              >
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="party">Party</option>
                <option value="work">Work</option>
                <option value="gym">Gym</option>
                <option value="date">Date</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-900 font-medium mb-3 text-sm tracking-wide uppercase flex items-center space-x-2">
                <FiTrendingUp className="text-amber-600" />
                <span>Season</span>
              </label>
              <select
                name="season"
                value={filters.season}
                onChange={handleFilterChange}
                className="w-full px-4 py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900"
              >
                <option value="all">All Seasons</option>
                <option value="summer">Summer</option>
                <option value="winter">Winter</option>
                <option value="spring">Spring</option>
                <option value="fall">Fall</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-900 font-medium mb-3 text-sm tracking-wide uppercase flex items-center space-x-2">
                <FiAward className="text-amber-600" />
                <span>Number of Results</span>
              </label>
              <select
                name="limit"
                value={filters.limit}
                onChange={handleFilterChange}
                className="w-full px-4 py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900"
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="15">15</option>
                <option value="20">20</option>
              </select>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={generateRecommendations}
            className="w-full bg-gray-900 text-white py-4 font-medium text-sm tracking-widest uppercase hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
            disabled={loading}
          >
            <HiOutlineSparkles className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Generating Recommendations...' : 'Generate Recommendations'}</span>
          </motion.button>
        </motion.div>

        {/* Results Section */}
        {recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
          >
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-bold text-gray-900 tracking-tight">
                Your Top {recommendations.length} Matches
              </h2>
              <div className="h-1 flex-1 ml-8 bg-gradient-to-r from-amber-600 to-transparent"></div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendations.map((rec, index) => (
                <motion.div 
                  key={index} 
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  whileHover={{ y: -8 }}
                  className="bg-white border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 group"
                >
                  {/* Image Section */}
                  <div className="relative bg-gray-100 h-64 overflow-hidden">
                    {rec.outfit?.image_url ? (
                      <img
                        src={rec.outfit.image_url}
                        alt={rec.outfit.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <HiOutlineSparkles className="text-7xl text-gray-300" />
                      </div>
                    )}
                    
                    {/* Rank Badge */}
                    <div className="absolute top-4 left-4 bg-gray-900 text-white w-12 h-12 flex items-center justify-center font-bold text-lg">
                      #{index + 1}
                    </div>
                    
                    {/* Score Badge */}
                    <div className="absolute top-4 right-4 bg-amber-600 text-white px-3 py-1 font-bold text-sm tracking-wide">
                      {(rec.overall_score * 100).toFixed(0)}% MATCH
                    </div>
                  </div>

                  {/* Content Section */}
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2 tracking-tight">
                      {rec.outfit?.name}
                    </h3>
                    <p className="text-gray-600 text-sm mb-4 font-light leading-relaxed">
                      {rec.outfit?.description}
                    </p>

                    {/* Score Breakdown */}
                    <div className="space-y-2 mb-4 pb-4 border-b border-gray-100">
                      <div className="flex justify-between text-xs text-gray-600">
                        <span className="font-medium">Style Match</span>
                        <span className="font-semibold text-gray-900">{(rec.scores.style_match * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-600">
                        <span className="font-medium">Comfort Level</span>
                        <span className="font-semibold text-gray-900">{(rec.scores.comfort * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-600">
                        <span className="font-medium">Trend Factor</span>
                        <span className="font-semibold text-gray-900">{(rec.scores.trend * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-600">
                        <span className="font-medium">Body Type Fit</span>
                        <span className="font-semibold text-gray-900">{(rec.scores.body_type * 100).toFixed(0)}%</span>
                      </div>
                    </div>

                    {/* Colors */}
                    {rec.outfit?.colors && rec.outfit.colors.length > 0 && (
                      <div className="flex gap-2 mb-4">
                        {rec.outfit.colors.slice(0, 3).map((color, i) => (
                          <span key={i} className="text-xs px-3 py-1 bg-gray-100 text-gray-700 font-medium tracking-wide uppercase">
                            {color}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Action Button */}
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => navigate(`/outfit/${rec.outfit?.id}`)}
                      className="w-full bg-gray-900 text-white py-3 font-medium text-xs tracking-widest uppercase hover:bg-gray-800 transition-colors flex items-center justify-center space-x-2"
                    >
                      <span>View Details</span>
                      <FiStar />
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {recommendations.length === 0 && !loading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="bg-white border border-gray-200 p-16 text-center"
          >
            <HiOutlineSparkles className="text-7xl text-amber-500 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-gray-900 mb-3 tracking-tight">No Recommendations Yet</h3>
            <p className="text-gray-600 font-light leading-relaxed max-w-md mx-auto">
              Set your preferences above and click generate to get personalized outfit recommendations!
            </p>
          </motion.div>
        )}
      </div>

      {/* Profile Completion Modal */}
      <AnimatePresence>
        {showProfileModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 px-4"
            onClick={() => setShowProfileModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              transition={{ type: "spring", duration: 0.5 }}
              className="bg-white max-w-md w-full p-8 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="inline-block mb-6"
                >
                  <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto">
                    <FiUser className="text-4xl text-amber-600" />
                  </div>
                </motion.div>
                
                <h3 className="text-2xl font-bold text-gray-900 mb-4 tracking-tight">
                  Complete Your Profile
                </h3>
                
                <p className="text-gray-600 font-light leading-relaxed mb-8">
                  To receive personalized recommendations, please complete your profile with your body type, style preferences, and other details.
                </p>
                
                <div className="space-y-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleGoToProfile}
                    className="w-full bg-gray-900 text-white py-4 font-medium text-sm tracking-widest uppercase hover:bg-gray-800 transition-colors flex items-center justify-center space-x-2"
                  >
                    <FiUser />
                    <span>Go to Profile</span>
                    <FiArrowRight />
                  </motion.button>
                  
                  <button
                    onClick={() => setShowProfileModal(false)}
                    className="w-full border border-gray-300 text-gray-700 py-4 font-medium text-sm tracking-widest uppercase hover:bg-gray-50 transition-colors"
                  >
                    Maybe Later
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Recommendations;
