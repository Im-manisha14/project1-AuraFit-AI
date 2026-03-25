import React, { useState, useEffect } from 'react';
import { outfitAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiStar, FiShoppingBag } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

const Trends = () => {
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrending();
  }, []);

  const loadTrending = async () => {
    try {
      const response = await outfitAPI.getTrending(6);
      setTrending(response.data.outfits || []);
    } catch (error) {
      console.error('Error loading trends:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-amber-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Loading fashion trends...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section with Luxury Fashion Store Background */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="relative text-white py-24 overflow-hidden"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?q=80&w=2070)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        {/* Elegant dark overlay with gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/75 to-black/70"></div>
        
        {/* Decorative elements with animation */}
        <div className="absolute inset-0">
          <div className="absolute top-10 right-10 w-80 h-80 bg-amber-600 opacity-10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-10 left-10 w-96 h-96 bg-amber-500 opacity-5 rounded-full blur-3xl"></div>
        </div>
        
        {/* Premium pattern overlay */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.03) 35px, rgba(255,255,255,.03) 70px)'
        }}></div>
        
        <div className="container mx-auto px-3 sm:px-4 md:px-6 relative z-10">
          <motion.div
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="max-w-4xl mx-auto text-center"
          >
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, type: "spring", delay: 0.3 }}
              className="inline-block mb-4 sm:mb-6"
            >
              <FiTrendingUp className="text-5xl sm:text-6xl lg:text-7xl text-amber-500 mx-auto drop-shadow-lg" />
            </motion.div>
            
            <motion.h1 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-3xl sm:text-5xl lg:text-6xl font-bold mb-4 sm:mb-6 tracking-tight drop-shadow-lg"
            >
              Fashion Trends 2026
            </motion.h1>
            
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            >
              <div className="w-20 sm:w-24 h-1 bg-amber-600 mx-auto mb-6"></div>
              <p className="text-base sm:text-lg md:text-xl text-gray-200 font-light leading-relaxed max-w-2xl mx-auto drop-shadow-md px-3">
                Discover the hottest fashion trends and stay ahead of the curve with our curated collection of luxury styles
              </p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mt-6 sm:mt-8 flex items-center justify-center space-x-2 text-amber-500"
            >
              <div className="w-8 sm:w-12 h-px bg-amber-500"></div>
              <span className="text-xs sm:text-sm tracking-widest uppercase drop-shadow-md">Curated for Excellence</span>
              <div className="w-8 sm:w-12 h-px bg-amber-500"></div>
            </motion.div>
          </motion.div>
        </div>
      </motion.div>

      <div className="container mx-auto px-3 sm:px-4 md:px-6 py-12 sm:py-14 md:py-16">
        {/* Trending Colors & Styles */}
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mb-12 sm:mb-16 md:mb-20"
        >
          <div className="bg-white border border-gray-200 shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-6 sm:p-8">
              <h2 className="text-2xl sm:text-3xl font-bold mb-2 tracking-tight">What's Hot Right Now</h2>
              <p className="text-gray-300 font-light text-sm sm:text-base">The season's most coveted colors and styles</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 sm:gap-10 md:gap-12 p-6 sm:p-8 md:p-10">
              <div>
                <div className="flex items-center space-x-3 mb-5 sm:mb-6">
                  <HiOutlineSparkles className="text-2xl sm:text-3xl text-amber-600" />
                  <h3 className="text-xl sm:text-2xl font-bold text-gray-900">Trending Colors</h3>
                </div>
                <div className="flex flex-wrap gap-2 sm:gap-3">
                  {[
                    { color: '#0A0A0A', name: 'Deep Black' },
                    { color: '#2C4A52', name: 'Dark Teal' },
                    { color: '#E8D5C4', name: 'Cream Beige' },
                    { color: '#C9A882', name: 'Sandy Tan' },
                    { color: '#5C5048', name: 'Earth Brown' }
                  ].map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      whileHover={{ scale: 1.1, y: -5 }}
                      className="group cursor-pointer"
                    >
                      <div 
                        className="w-20 h-20 rounded-full shadow-md group-hover:shadow-xl transition-shadow"
                        style={{ background: item.color }}
                      ></div>
                      <p className="text-center text-xs mt-2 text-gray-700 font-medium">{item.name}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
              
              <div>
                <div className="flex items-center space-x-3 mb-6">
                  <FiStar className="text-3xl text-amber-600" />
                  <h3 className="text-2xl font-bold text-gray-900">Trending Styles</h3>
                </div>
                <ul className="space-y-3">
                  {[
                    'Oversized & Relaxed Fits',
                    'Minimalist Aesthetic',
                    'Sustainable Fashion',
                    'Vintage Revival',
                    'Athleisure Fusion'
                  ].map((style, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="flex items-center space-x-3 text-gray-700"
                    >
                      <div className="w-2 h-2 bg-amber-600 rounded-full"></div>
                      <span className="text-lg font-light">{style}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Trending Outfits */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 tracking-tight mb-2">
                Top Trending Outfits
              </h2>
              <p className="text-gray-600 font-light">Exclusive collection for men and women</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {trending.map((outfit, index) => (
              <motion.div
                key={outfit.id}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -12 }}
                className="group cursor-pointer"
                onClick={() => navigate('/explore-trends')}
              >
                <div className="relative overflow-hidden bg-white shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-200">
                  {/* Trending Badge */}
                  <motion.div 
                    initial={{ x: -100 }}
                    whileInView={{ x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: index * 0.1 + 0.2 }}
                    className="absolute top-4 left-0 bg-gradient-to-r from-amber-600 to-amber-500 text-white px-4 py-2 z-10 shadow-md flex items-center space-x-2"
                  >
                    <FiStar className="text-white" />
                    <span className="font-semibold text-xs tracking-widest uppercase">#{index + 1} Trending</span>
                  </motion.div>

                  <div className="relative h-96 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
                    {outfit.image_url ? (
                      <img
                        src={outfit.image_url}
                        alt={outfit.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                        onError={(e) => { e.target.onerror = null; e.target.src = `https://loremflickr.com/600/900/fashion,outfit?lock=${outfit.id}`; }}
                      />
                    ) : (
                      <img
                        src={
                          index === 0 
                            ? 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=2020' // Elegant women's fashion
                            : index === 1 
                            ? 'https://images.unsplash.com/photo-1617137968427-85924c800a22?q=80&w=2070' // Minimalist modern outfit
                            : index === 2 
                            ? 'https://images.unsplash.com/photo-1523398002811-999ca8dec234?q=80&w=2005' // Summer casual wear
                            : index === 3
                            ? 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=2070' // Men's formal wear
                            : index === 4
                            ? 'https://images.unsplash.com/photo-1539533018447-63fcce2678e3?q=80&w=2070' // Luxury accessories
                            : 'https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?q=80&w=2069' // Designer collection
                        }
                        alt={outfit.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                      />
                    )}
                    
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-50 group-hover:opacity-30 transition-opacity duration-500"></div>
                    
                    {/* Trend Score Badge */}
                    <div className="absolute bottom-4 right-4 bg-white bg-opacity-90 backdrop-blur-sm px-4 py-2 rounded-full flex items-center space-x-2">
                      <span className="text-amber-600 font-bold text-lg">⭐</span>
                      <span className="text-gray-900 font-semibold">{outfit.trend_score?.toFixed(1)}</span>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-amber-600 transition-colors tracking-tight">
                        {outfit.name}
                      </h3>
                      <motion.div
                        whileHover={{ rotate: 180, scale: 1.2 }}
                        transition={{ duration: 0.3 }}
                      >
                        <HiOutlineSparkles className="text-amber-500 text-2xl" />
                      </motion.div>
                    </div>
                    
                    {outfit.description && (
                      <p className="text-gray-600 text-sm line-clamp-2 mb-4 font-light leading-relaxed">
                        {outfit.description}
                      </p>
                    )}
                    
                    <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                      <div className="flex items-center space-x-2 flex-wrap gap-2">
                        <span className="inline-block px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium tracking-wide uppercase">
                          {outfit.style_type}
                        </span>
                        <span className="inline-block px-3 py-1 bg-amber-50 text-amber-700 text-xs font-medium tracking-wide uppercase">
                          {outfit.occasion}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      <span className="text-amber-600 font-medium text-sm group-hover:underline flex items-center space-x-1">
                        <span>Explore Details</span>
                        <span className="group-hover:translate-x-1 transition-transform">→</span>
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {trending.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white border border-gray-200 shadow-lg text-center py-16 px-6"
            >
              <FiTrendingUp className="text-7xl text-gray-300 mb-6 mx-auto" />
              <h3 className="text-2xl font-bold mb-3 text-gray-900">No Trending Data Available</h3>
              <p className="text-gray-600 font-light max-w-md mx-auto">
                Check back later for the latest fashion trends and exclusive collections!
              </p>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Trends;
