import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { recommendationAPI, userAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { FiStar, FiTrendingUp, FiCalendar, FiAward, FiHeart, FiUser, FiArrowRight, FiShoppingBag } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

const COLLECTION_META = {
  trending:   { title: 'Trending Right Now',   icon: '🔥' },
  seasonal:   { title: 'Seasonal Picks',       icon: '🌤' },
  casual:     { title: 'Casual Collection',    icon: '👕' },
  formal:     { title: 'Formal & Work Wear',   icon: '💼' },
  sports:     { title: 'Sports & Athleisure',  icon: '🏋' },
  minimalist: { title: 'Minimalist Fashion',   icon: '🎯' },
  party:      { title: 'Party & Date Night',   icon: '🎉' },
};

const SHOP_LABELS = {
  myntra:        { label: 'Myntra',    color: '#FF3F6C' },
  flipkart:      { label: 'Flipkart', color: '#2874F0' },
  ajio:          { label: 'Ajio',     color: '#E31E25' },
  meesho:        { label: 'Meesho',   color: '#9B2D8E' },
  nykaa_fashion: { label: 'Nykaa',    color: '#FC2779' },
  amazon:        { label: 'Amazon',   color: '#FF9900' },
  hm:            { label: 'H&M',      color: '#E50010' },
  zara:          { label: 'Zara',     color: '#111111' },
};

const GENDER_BADGE = {
  female: { label: 'Women', bg: '#FFF0F6', color: '#C2185B' },
  male:   { label: 'Men',   bg: '#E3F2FD', color: '#1565C0' },
  unisex: { label: 'Unisex', bg: '#F3E5F5', color: '#6A1B9A' },
};

const GenderBadge = ({ gender }) => {
  const g = (gender || 'unisex').toLowerCase();
  const badge = GENDER_BADGE[g] || GENDER_BADGE.unisex;
  return (
    <span
      className="text-xs font-bold px-2 py-0.5 rounded-full tracking-wide uppercase"
      style={{ background: badge.bg, color: badge.color }}
    >
      {badge.label}
    </span>
  );
};

const Recommendations = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const autoGenerateRef = useRef(location.state?.autoGenerate || false);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileComplete, setProfileComplete] = useState(true);
  const [userGender, setUserGender] = useState('');
  const [filters, setFilters] = useState({
    occasion: 'casual',
    season: 'all',
    limit: 10,
  });
  const [collections, setCollections] = useState({});
  const [collectionsLoading, setCollectionsLoading] = useState(false);
  const [shopOpen, setShopOpen] = useState(null);

  useEffect(() => {
    checkProfileStatus();
    loadCollections();
  }, []);

  const loadCollections = async () => {
    setCollectionsLoading(true);
    try {
      const res = await recommendationAPI.getCollections({ season: 'all', limit: 8 });
      setCollections(res.data.collections || {});
    } catch (err) {
      console.error('Error loading collections:', err);
    } finally {
      setCollectionsLoading(false);
    }
  };

  const checkProfileStatus = async () => {
    try {
      const profileRes = await userAPI.getProfile();
      const prefsRes = await userAPI.getPreferences();
      
      const profile = profileRes.data.profile;
      const prefs = prefsRes.data.preferences;
      
      // Check if essential profile fields are filled
      // (preferred_styles is optional - don't gate on it)
      const isComplete = !!(profile?.body_type && profile?.age && profile?.gender);
      
      setProfileComplete(isComplete);
      if (profile?.gender) setUserGender(profile.gender.toLowerCase());

      // Auto-generate if we just arrived from profile save
      if (autoGenerateRef.current && isComplete) {
        autoGenerateRef.current = false;
        setLoading(true);
        try {
          const response = await recommendationAPI.generate({ occasion: 'casual', season: 'all', limit: 10 });
          setRecommendations(response.data.recommendations || []);
        } catch (err) {
          console.error('Auto-generate error:', err);
        } finally {
          setLoading(false);
        }
      } else if (autoGenerateRef.current && !isComplete) {
        autoGenerateRef.current = false;
        setShowProfileModal(true);
      }
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
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="text-xl font-bold text-gray-900 tracking-tight leading-snug">
                        {rec.outfit?.name}
                      </h3>
                      <GenderBadge gender={rec.outfit?.gender} />
                    </div>
                    <p className="text-gray-600 text-sm mb-4 font-light leading-relaxed">
                      {rec.outfit?.description}
                    </p>

                    {/* Occasion + Season tags */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {rec.outfit?.occasion && (
                        <span className="text-xs px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full capitalize font-medium">
                          {rec.outfit.occasion}
                        </span>
                      )}
                      {rec.outfit?.season && rec.outfit.season !== 'all' && (
                        <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-full capitalize font-medium">
                          {rec.outfit.season}
                        </span>
                      )}
                      {rec.outfit?.style_type && (
                        <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full capitalize font-medium">
                          {rec.outfit.style_type}
                        </span>
                      )}
                    </div>

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

                    {/* Dress Structure */}
                    {(rec.outfit?.top || rec.outfit?.bottom || rec.outfit?.shoes || rec.outfit?.accessories?.length > 0) && (
                      <div className="mb-4 pb-4 border-b border-gray-100">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">Outfit Pieces</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                          {rec.outfit?.top && (
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Top</span>
                              <span className="text-xs text-gray-700 leading-snug">{rec.outfit.top}</span>
                            </div>
                          )}
                          {rec.outfit?.bottom && (
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Bottom</span>
                              <span className="text-xs text-gray-700 leading-snug">{rec.outfit.bottom}</span>
                            </div>
                          )}
                          {rec.outfit?.shoes && (
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Shoes</span>
                              <span className="text-xs text-gray-700 leading-snug">{rec.outfit.shoes}</span>
                            </div>
                          )}
                          {rec.outfit?.accessories?.length > 0 && (
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Acc</span>
                              <span className="text-xs text-gray-700 leading-snug">{rec.outfit.accessories.join(', ')}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

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
                      className="w-full bg-gray-900 text-white py-3 font-medium text-xs tracking-widest uppercase hover:bg-gray-800 transition-colors flex items-center justify-center space-x-2 mb-2"
                    >
                      <span>View Details</span>
                      <FiStar />
                    </motion.button>

                    {/* Shop Links */}
                    {rec.outfit?.shopping_links && Object.keys(rec.outfit.shopping_links).length > 0 && (
                      <div>
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setShopOpen(shopOpen === `rec-${index}` ? null : `rec-${index}`)}
                          className="w-full border border-amber-600 text-amber-700 py-2.5 font-medium text-xs tracking-widest uppercase hover:bg-amber-50 transition-colors flex items-center justify-center gap-2"
                        >
                          <FiShoppingBag />
                          <span>{shopOpen === `rec-${index}` ? 'Hide Links' : 'Shop Now'}</span>
                        </motion.button>
                        {shopOpen === `rec-${index}` && (
                          <motion.div
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="grid grid-cols-4 gap-1 mt-2"
                          >
                            {Object.entries(rec.outfit.shopping_links).map(([platform, url]) => {
                              const s = SHOP_LABELS[platform];
                              if (!s) return null;
                              return (
                                <a
                                  key={platform}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-center text-xs py-1.5 font-semibold border transition-all hover:text-white truncate"
                                  style={{ borderColor: s.color, color: s.color }}
                                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = s.color; e.currentTarget.style.color = '#fff'; }}
                                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = s.color; }}
                                >
                                  {s.label}
                                </a>
                              );
                            })}
                          </motion.div>
                        )}
                      </div>
                    )}
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

        {/* Collections Section */}
        {(collectionsLoading || Object.keys(collections).length > 0) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16"
          >
            <div className="flex items-center mb-10">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 tracking-tight whitespace-nowrap">Style Collections</h2>
                {userGender && (
                  <p className="text-sm text-gray-500 mt-1">
                    Curated <span className="font-semibold text-amber-600">
                      {userGender === 'female' ? "women's" : userGender === 'male' ? "men's" : ''}
                    </span> fashion for you
                  </p>
                )}
              </div>
              <div className="h-1 flex-1 ml-8 bg-gradient-to-r from-amber-600 to-transparent"></div>
            </div>

            {collectionsLoading ? (
              <div className="text-center py-12 text-gray-400">
                <HiOutlineSparkles className="text-5xl mx-auto mb-3 animate-pulse" />
                <p className="font-light">Loading style collections…</p>
              </div>
            ) : (
              Object.entries(COLLECTION_META).map(([key, meta]) => {
                const outfits = collections[key];
                if (!outfits || outfits.length === 0) return null;
                return (
                  <div key={key} className="mb-14">
                    {/* Row Header */}
                    <div className="flex items-center gap-3 mb-5">
                      <span className="text-2xl">{meta.icon}</span>
                      <h3 className="text-xl font-bold text-gray-900 tracking-tight">{meta.title}</h3>
                      <span className="text-sm text-gray-400 font-light">{outfits.length} looks</span>
                    </div>

                    {/* Horizontal Scroll Row */}
                    <div
                      className="flex gap-5 pb-4"
                      style={{ overflowX: 'auto', overflowY: 'visible', scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                    >
                      {outfits.map((outfit, idx) => (
                        <motion.div
                          key={outfit.id}
                          initial={{ opacity: 0, x: 20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: idx * 0.04 }}
                          className="flex-shrink-0 w-60 bg-white border border-gray-200 overflow-visible shadow-sm hover:shadow-md transition-all group"
                        >
                          {/* Outfit Image */}
                          <div className="relative h-48 bg-gray-100 overflow-hidden">
                            {outfit.image_url ? (
                              <img
                                src={outfit.image_url}
                                alt={outfit.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <HiOutlineSparkles className="text-5xl text-gray-300" />
                              </div>
                            )}
                            {outfit.match_score != null && (
                              <div className="absolute top-2 right-2 bg-amber-600 text-white px-2 py-0.5 text-xs font-bold">
                                {(outfit.match_score * 100).toFixed(0)}%
                              </div>
                            )}
                          </div>

                          {/* Card Body */}
                          <div className="p-4">
                            <div className="flex items-start justify-between gap-1 mb-1">
                              <p className="font-semibold text-gray-900 text-sm truncate flex-1" title={outfit.name}>{outfit.name}</p>
                              <GenderBadge gender={outfit.gender} />
                            </div>
                            <p className="text-xs text-gray-500 mb-2 capitalize tracking-wide">{outfit.style_type}</p>

                            {/* Dress Structure */}
                            {(outfit.top || outfit.bottom || outfit.shoes || outfit.accessories?.length > 0) && (
                              <div className="mb-3 pb-2 border-b border-gray-100">
                                <div className="space-y-0.5">
                                  {outfit.top && (
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Top</span>
                                      <span className="text-gray-600 leading-snug">{outfit.top}</span>
                                    </div>
                                  )}
                                  {outfit.bottom && (
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Bottom</span>
                                      <span className="text-gray-600 leading-snug">{outfit.bottom}</span>
                                    </div>
                                  )}
                                  {outfit.shoes && (
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Shoes</span>
                                      <span className="text-gray-600 leading-snug">{outfit.shoes}</span>
                                    </div>
                                  )}
                                  {outfit.accessories?.length > 0 && (
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Acc</span>
                                      <span className="text-gray-600 leading-snug">{outfit.accessories.join(', ')}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Shop Button + Inline Links */}
                            {outfit.shopping_links && Object.keys(outfit.shopping_links).length > 0 && (
                              <div>
                                <button
                                  onClick={() => setShopOpen(
                                    shopOpen === `${key}-${outfit.id}` ? null : `${key}-${outfit.id}`
                                  )}
                                  className="w-full flex items-center justify-center gap-1.5 bg-gray-900 text-white py-2 text-xs font-medium tracking-wider uppercase hover:bg-gray-700 transition-colors"
                                >
                                  <FiShoppingBag className="text-xs" />
                                  <span>{shopOpen === `${key}-${outfit.id}` ? 'Hide' : 'Shop Now'}</span>
                                </button>
                                {shopOpen === `${key}-${outfit.id}` && (
                                  <motion.div
                                    initial={{ opacity: 0, y: -4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="grid grid-cols-4 gap-1 mt-2"
                                  >
                                    {Object.entries(outfit.shopping_links).map(([platform, url]) => {
                                      const s = SHOP_LABELS[platform];
                                      if (!s) return null;
                                      return (
                                        <a
                                          key={platform}
                                          href={url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-center text-xs py-1.5 font-semibold border transition-all hover:text-white truncate"
                                          style={{ borderColor: s.color, color: s.color }}
                                          onMouseEnter={e => { e.currentTarget.style.backgroundColor = s.color; e.currentTarget.style.color = '#fff'; }}
                                          onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = s.color; }}
                                        >
                                          {s.label}
                                        </a>
                                      );
                                    })}
                                  </motion.div>
                                )}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                );
              })
            )}
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
