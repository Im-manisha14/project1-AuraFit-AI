import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { recommendationAPI, userAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { FiStar, FiTrendingUp, FiCalendar, FiAward, FiUser, FiArrowRight, FiShoppingBag } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

const COLLECTION_META = {
  skin_tone:  { title: 'Based on Your Skin Tone', icon: '🎨' },
  body_shape: { title: 'For Your Body Shape',      icon: '✨' },
  trending:   { title: 'Trending Right Now',       icon: '🔥' },
  seasonal:   { title: 'Seasonal Picks',           icon: '🌤' },
  casual:     { title: 'Casual Collection',        icon: '👕' },
  formal:     { title: 'Formal & Work Wear',       icon: '💼' },
  sports:     { title: 'Sports & Athleisure',      icon: '🏋' },
  minimalist: { title: 'Minimalist Fashion',       icon: '🎯' },
  party:      { title: 'Party & Date Night',       icon: '🎉' },
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
const SHOP_LABELS = {
  myntra:   { label: 'Myntra',    color: '#FF3F6C' },
  flipkart: { label: 'Flipkart', color: '#2874F0' },
  ajio:     { label: 'Ajio',     color: '#E31E25' },
  meesho:   { label: 'Meesho',   color: '#9B2D8E' },
  nykaa:    { label: 'Nykaa',    color: '#FC2779' },
  amazon:   { label: 'Amazon',   color: '#FF9900' },
  hm:       { label: 'H&M',      color: '#E50010' },
  zara:     { label: 'Zara',     color: '#111111' },
};

const Recommendations = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const autoGenerateRef = useRef(location.state?.autoGenerate || false);
  const [recommendations, setRecommendations] = useState([]);
  const [similarRecommendations, setSimilarRecommendations] = useState([]);
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
  const [failedImages, setFailedImages] = useState(new Set());


  useEffect(() => {
    checkProfileStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadCollections = async () => {
    setCollectionsLoading(true);
    try {
      const res = await recommendationAPI.getCollections({ season: 'all', limit: 8 });
      setCollections(res.data || {});
    } catch (err) {
      console.error('Error loading collections:', err);
    } finally {
      setCollectionsLoading(false);
    }
  };

  const checkProfileStatus = async () => {
    try {
      const profileRes = await userAPI.getProfile();
      await userAPI.getPreferences();
      
      const profile = profileRes.data.profile;
      
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
          loadCollections();
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
      setSimilarRecommendations(response.data.similar_recommendations || []);
      loadCollections();
    } catch (error) {
      console.error('Error generating recommendations:', error);
      // Only show profile modal if the server says profile is incomplete (400)
      if (error.response?.status === 400) {
        setShowProfileModal(true);
      }
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
      <div className="container mx-auto px-3 sm:px-4 md:px-6 py-8 sm:py-12">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="bg-white border border-gray-200 p-5 sm:p-6 md:p-8 shadow-sm mb-8 sm:mb-12"
        >
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-5 sm:mb-6 tracking-tight">Customize Your Recommendations</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-5 md:gap-6 mb-6 sm:mb-8">
            <div>
              <label className="block text-gray-900 font-medium mb-2 sm:mb-3 text-xs sm:text-sm tracking-wide uppercase flex items-center space-x-1 sm:space-x-2">
                <FiCalendar className="text-amber-600 text-sm sm:text-base" />
                <span>Occasion</span>
              </label>
              <select
                name="occasion"
                value={filters.occasion}
                onChange={handleFilterChange}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900 text-sm"
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
              <label className="block text-gray-900 font-medium mb-2 sm:mb-3 text-xs sm:text-sm tracking-wide uppercase flex items-center space-x-1 sm:space-x-2">
                <FiTrendingUp className="text-amber-600 text-sm sm:text-base" />
                <span>Season</span>
              </label>
              <select
                name="season"
                value={filters.season}
                onChange={handleFilterChange}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900 text-sm"
              >
                <option value="all">All Seasons</option>
                <option value="summer">Summer</option>
                <option value="winter">Winter</option>
                <option value="spring">Spring</option>
                <option value="fall">Fall</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-900 font-medium mb-2 sm:mb-3 text-xs sm:text-sm tracking-wide uppercase flex items-center space-x-1 sm:space-x-2">
                <FiAward className="text-amber-600 text-sm sm:text-base" />
                <span>Results</span>
              </label>
              <select
                name="limit"
                value={filters.limit}
                onChange={handleFilterChange}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-200 focus:outline-none focus:border-amber-600 transition-colors bg-gray-50 text-gray-900 text-sm"
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
            className="w-full bg-gray-900 text-white py-3 sm:py-4 font-medium text-xs sm:text-sm tracking-widest uppercase hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2 min-h-10 sm:min-h-12"
            disabled={loading}
          >
            <HiOutlineSparkles className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Generating...' : 'Generate Recommendations'}</span>
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
            
            <div className="recommendations-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
              {recommendations.filter(rec => !failedImages.has(rec.outfit?.id)).map((rec, index) => (
                <motion.div 
                  key={index} 
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  whileHover={{ y: -8 }}
                  className="recommendation-card h-full flex flex-col bg-white border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 group"
                >
                  {/* Image Section */}
                  <div className="relative bg-gray-100 h-64 overflow-hidden flex-shrink-0">
                    {rec.outfit?.image_url && !failedImages.has(rec.outfit?.id) ? (
                      <img
                        src={rec.outfit.image_url}
                        alt={rec.outfit.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => { 
                          if (rec.outfit?.additional_images && rec.outfit.additional_images.length > 0 && e.target.src !== rec.outfit.additional_images[0]) {
                            e.target.src = rec.outfit.additional_images[0];
                          } else {
                            setFailedImages(prev => new Set(prev).add(rec.outfit?.id));
                          }
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                        <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height="4em" width="4em" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                        <p className="mt-2 text-sm font-medium">Image unavailable</p>
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
                  <div className="recommendation-card-content p-6 flex flex-col flex-1">
                    <div className="recommendation-card-title flex items-start justify-between gap-2 mb-2">
                      <h3 className="text-xl font-bold text-gray-900 tracking-tight leading-snug">
                        {rec.outfit?.name}
                      </h3>
                      <GenderBadge gender={rec.outfit?.gender} />
                    </div>
                    <p className="recommendation-card-description text-gray-600 text-sm mb-4 font-light leading-relaxed">
                      {rec.outfit?.description}
                    </p>

                    {/* Occasion + Season tags */}
                    <div className="recommendation-card-tags flex flex-wrap gap-1 mb-4 items-center">
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
                    {(() => {
                      const pTop = rec.outfit?.top || (rec.outfit?.name?.toLowerCase().includes('dress') ? rec.outfit.name : 'Styled Top');
                      const pBottom = rec.outfit?.bottom || (rec.outfit?.name?.toLowerCase().includes('dress') ? 'Flowy Silhouette Hem' : 'Matching Bottom');
                      const pShoes = rec.outfit?.shoes || (rec.outfit?.occasion === 'party' || rec.outfit?.style_type === 'glamorous' ? 'Stiletto Heels' : rec.outfit?.occasion === 'work' ? 'Pointed Pumps' : rec.outfit?.style_type === 'ethnic' ? 'Embroidered Juttis' : 'Classic White Sneakers');
                      const pAcc = (rec.outfit?.accessories && rec.outfit.accessories.length > 0)
                        ? (Array.isArray(rec.outfit.accessories) ? rec.outfit.accessories.join(', ') : rec.outfit.accessories)
                        : (rec.outfit?.style_type === 'ethnic' ? 'Traditional Jhumkas' : rec.outfit?.occasion === 'party' ? 'Evening Clutch' : 'Minimalist Watch');
                      return (
                        <div className="mb-4 pb-4 border-b border-gray-100">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">Outfit Pieces</p>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Top</span>
                              <span className="text-xs text-gray-700 leading-snug truncate" title={pTop}>{pTop}</span>
                            </div>
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Bottom</span>
                              <span className="text-xs text-gray-700 leading-snug truncate" title={pBottom}>{pBottom}</span>
                            </div>
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Shoes</span>
                              <span className="text-xs text-gray-700 leading-snug truncate" title={pShoes}>{pShoes}</span>
                            </div>
                            <div className="flex items-start gap-1.5">
                              <span className="text-xs text-amber-600 font-bold uppercase tracking-wide mt-0.5">Acc</span>
                              <span className="text-xs text-gray-700 leading-snug truncate" title={pAcc}>{pAcc}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })()}

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

                    {/* Footer Section: Product Details & Action Buttons */}
                    <div className="recommendation-card-footer mt-auto pt-3 border-t border-gray-100">
                      {/* Product Details (Price, Retailer, MRP & Discount) */}
                      <div className="flex flex-col gap-1 mb-4">
                        <div className="flex justify-between items-center min-h-[20px]">
                          <span className="text-xs font-bold text-gray-800 uppercase tracking-wide truncate">
                            {rec.outfit?.retailer || rec.outfit?.store || rec.outfit?.brand}
                          </span>
                          {rec.outfit?.availability && (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider flex-shrink-0 ${
                              rec.outfit.availability === 'LIMITED' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {rec.outfit.availability}
                            </span>
                          )}
                        </div>
                        <div className="flex items-baseline gap-2 flex-wrap min-h-[28px]">
                          {rec.outfit?.price ? (
                            <span className="text-lg font-bold text-amber-600">
                              {new Intl.NumberFormat('en-IN', { style: 'currency', currency: rec.outfit.currency || 'INR' }).format(rec.outfit.price)}
                            </span>
                          ) : null}
                          {rec.outfit?.original_price && rec.outfit.original_price > rec.outfit.price && (
                            <span className="text-xs text-gray-400 line-through">
                              MRP {new Intl.NumberFormat('en-IN', { style: 'currency', currency: rec.outfit.currency || 'INR' }).format(rec.outfit.original_price)}
                            </span>
                          )}
                          {rec.outfit?.discount && (
                            <span className="text-xs font-bold text-green-600">
                              {rec.outfit.discount}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-col gap-2 mb-2">
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigate(`/outfit/${rec.outfit?.id}`)}
                          className="w-full bg-white border border-gray-900 text-gray-900 py-3 font-medium text-xs tracking-widest uppercase hover:bg-gray-50 transition-colors flex items-center justify-center space-x-2"
                        >
                          <span>View Details</span>
                          <FiStar />
                        </motion.button>
                        
                        {(!rec.outfit?.in_stock) ? (
                          <button disabled className="w-full bg-gray-200 text-gray-500 py-3 font-medium text-xs tracking-widest uppercase flex items-center justify-center space-x-2 cursor-not-allowed">
                            <span>Out of Stock</span>
                          </button>
                        ) : (rec.outfit?.exact_product_link_available && (rec.outfit.shopping_url || rec.outfit.product_url)) ? (
                          <div>
                            <motion.a
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              href={rec.outfit.shopping_url || rec.outfit.product_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="w-full bg-amber-600 text-white py-3 font-medium text-xs tracking-widest uppercase hover:bg-amber-700 transition-colors flex items-center justify-center space-x-2"
                            >
                              <FiShoppingBag />
                              <span>Shop Now</span>
                            </motion.a>
                            {rec.outfit?.shopping_links && Object.keys(rec.outfit.shopping_links).length > 1 && (
                              <div className="grid grid-cols-4 gap-1 mt-2">
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
                              </div>
                            )}
                          </div>
                        ) : (
                          <button disabled className="w-full bg-gray-100 text-gray-400 py-3 font-medium text-xs tracking-widest uppercase flex items-center justify-center space-x-2 cursor-not-allowed border border-gray-200">
                            <span>Shopping Link Unavailable</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Similar Recommendations Section (Live SerpApi Products) */}
        {similarRecommendations.length > 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-16"
          >
            <div className="flex items-center mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 tracking-tight">
                  Similar Real Products
                </h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  Curated live from Google Shopping matching your occasion and style
                </p>
              </div>
              <div className="h-1 flex-1 ml-8 bg-gradient-to-r from-amber-600 to-transparent"></div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-stretch">
              {similarRecommendations
                .filter(sim => !failedImages.has(sim.id) && !failedImages.has(sim.external_id) && sim.image_url)
                .map((sim, sIdx) => (
                <div key={sIdx} className="bg-white border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-all p-4 flex flex-col h-full">
                  <div className="h-56 overflow-hidden bg-gray-100 mb-3 relative flex-shrink-0">
                    <img
                      src={sim.image_url}
                      alt={sim.name || sim.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        if (sim.additional_images && sim.additional_images.length > 0 && e.target.src !== sim.additional_images[0]) {
                          e.target.src = sim.additional_images[0];
                        } else {
                          setFailedImages(prev => new Set(prev).add(sim.id || sim.external_id));
                        }
                      }}
                    />
                    <span className="absolute top-2 right-2 bg-gray-900 text-white text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider">
                      Live Offer
                    </span>
                  </div>
                  <div className="flex-1 flex flex-col">
                    <span className="text-[11px] font-bold text-gray-700 uppercase tracking-wider block mb-1 truncate">
                      {sim.retailer || sim.store}
                    </span>
                    <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-2 leading-snug min-h-[2.5rem]">
                      {sim.name || sim.title}
                    </h4>
                    <p className="text-base font-bold text-amber-600 mb-3">
                      {new Intl.NumberFormat('en-IN', { style: 'currency', currency: sim.currency || 'INR' }).format(sim.price)}
                    </p>
                  </div>
                  <div className="flex flex-col gap-1.5 mt-auto">
                    {sim.id && (
                      <button
                        onClick={() => navigate(`/outfit/${sim.id}`)}
                        className="w-full bg-white border border-gray-900 text-gray-900 py-2 text-xs font-semibold uppercase tracking-wider hover:bg-gray-50 flex items-center justify-center gap-1.5"
                      >
                        <FiStar className="text-xs" />
                        <span>View Details</span>
                      </button>
                    )}
                    <a
                      href={sim.shopping_url || sim.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full bg-amber-600 text-white py-2 text-xs font-semibold uppercase tracking-wider text-center hover:bg-amber-700 flex items-center justify-center gap-1.5"
                    >
                      <FiShoppingBag />
                      <span>Shop Now</span>
                    </a>
                  </div>
                </div>
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
            <h3 className="text-2xl font-bold text-gray-900 mb-3 tracking-tight">Live shopping results are temporarily unavailable</h3>
            <p className="text-gray-600 font-light leading-relaxed max-w-md mx-auto">
              Please adjust your filters and try generating again.
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
                      className="flex gap-5 pb-4 items-stretch"
                      style={{ overflowX: 'auto', overflowY: 'visible', scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                    >
                      {outfits.filter(outfit => !failedImages.has(outfit.id)).map((outfit, idx) => (
                        <motion.div
                          key={outfit.id}
                          initial={{ opacity: 0, x: 20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: idx * 0.04 }}
                          className="flex-shrink-0 w-60 bg-white border border-gray-200 overflow-visible shadow-sm hover:shadow-md transition-all group flex flex-col"
                        >
                          {/* Outfit Image */}
                          <div className="relative h-48 bg-gray-100 overflow-hidden flex-shrink-0">
                            {outfit.image_url && !failedImages.has(outfit.id) ? (
                              <img
                                src={outfit.image_url}
                                alt={outfit.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                onError={() => { 
                                  setFailedImages(prev => new Set(prev).add(outfit.id));
                                }}
                              />
                            ) : (
                              <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                                <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height="4em" width="4em" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                                <p className="mt-2 text-sm font-medium">Image unavailable</p>
                              </div>
                            )}
                            {outfit.match_score != null && (
                              <div className="absolute top-2 right-2 bg-amber-600 text-white px-2 py-0.5 text-xs font-bold">
                                {(outfit.match_score * 100).toFixed(0)}%
                              </div>
                            )}
                          </div>

                          {/* Card Body */}
                          <div className="p-4 flex-1 flex flex-col">
                            <div className="flex items-start justify-between gap-1 mb-1">
                              <p className="font-semibold text-gray-900 text-sm truncate flex-1" title={outfit.name}>{outfit.name}</p>
                              <GenderBadge gender={outfit.gender} />
                            </div>
                            <p className="text-xs text-gray-500 mb-2 capitalize tracking-wide">{outfit.style_type}</p>

                            {/* Dress Structure */}
                            {(() => {
                              const pTop = outfit.top || (outfit.name?.toLowerCase().includes('dress') ? outfit.name : 'Styled Top');
                              const pBottom = outfit.bottom || (outfit.name?.toLowerCase().includes('dress') ? 'Flowy Silhouette Hem' : 'Matching Bottom');
                              const pShoes = outfit.shoes || (outfit.occasion === 'party' || outfit.style_type === 'glamorous' ? 'Stiletto Heels' : outfit.occasion === 'work' ? 'Pointed Pumps' : outfit.style_type === 'ethnic' ? 'Embroidered Juttis' : 'Classic White Sneakers');
                              const pAcc = (outfit.accessories && outfit.accessories.length > 0)
                                ? (Array.isArray(outfit.accessories) ? outfit.accessories.join(', ') : outfit.accessories)
                                : (outfit.style_type === 'ethnic' ? 'Traditional Jhumkas' : outfit.occasion === 'party' ? 'Evening Clutch' : 'Minimalist Watch');
                              return (
                                <div className="mb-3 pb-2 border-b border-gray-100">
                                  <div className="space-y-0.5">
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Top</span>
                                      <span className="text-gray-600 leading-snug truncate" title={pTop}>{pTop}</span>
                                    </div>
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Bottom</span>
                                      <span className="text-gray-600 leading-snug truncate" title={pBottom}>{pBottom}</span>
                                    </div>
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Shoes</span>
                                      <span className="text-gray-600 leading-snug truncate" title={pShoes}>{pShoes}</span>
                                    </div>
                                    <div className="flex gap-1 text-xs">
                                      <span className="text-amber-600 font-bold uppercase w-12 flex-shrink-0">Acc</span>
                                      <span className="text-gray-600 leading-snug truncate" title={pAcc}>{pAcc}</span>
                                    </div>
                                  </div>
                                </div>
                              );
                            })()}

                            {/* Footer Section: Product Details & Shop Button */}
                            <div className="mt-auto pt-2 border-t border-gray-100">
                              <div className="flex justify-between items-center mb-3 min-h-[1.5rem]">
                                {outfit.brand && (
                                  <span className="text-xs font-bold text-gray-800 uppercase truncate mr-2">
                                    {outfit.brand}
                                  </span>
                                )}
                                {outfit.price && (
                                  <span className="text-sm font-bold text-amber-600 flex-shrink-0">
                                    {new Intl.NumberFormat('en-IN', { style: 'currency', currency: outfit.currency || 'INR' }).format(outfit.price)}
                                  </span>
                                )}
                              </div>

                              {(!outfit.in_stock) ? (
                                <button disabled className="w-full flex items-center justify-center gap-1.5 bg-gray-200 text-gray-500 py-2.5 text-xs font-medium tracking-wider uppercase cursor-not-allowed">
                                  <span>Out of Stock</span>
                                </button>
                              ) : (outfit.exact_product_link_available && (outfit.shopping_url || outfit.product_url)) ? (
                                <div>
                                  <a
                                    href={outfit.shopping_url || outfit.product_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-full flex items-center justify-center gap-1.5 bg-gray-900 text-white py-2.5 text-xs font-medium tracking-wider uppercase hover:bg-gray-700 transition-colors"
                                  >
                                    <FiShoppingBag className="text-xs" />
                                    <span>Shop Now</span>
                                  </a>
                                  {outfit.shopping_links && Object.keys(outfit.shopping_links).length > 1 && (
                                    <div className="grid grid-cols-4 gap-1 mt-2">
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
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <button disabled className="w-full flex items-center justify-center gap-1.5 bg-gray-100 text-gray-400 py-2.5 text-xs font-medium tracking-wider uppercase cursor-not-allowed border border-gray-200">
                                  <span>Shopping Link Unavailable</span>
                                </button>
                              )}
                            </div>
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
