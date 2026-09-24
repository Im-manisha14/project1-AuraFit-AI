import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { outfitAPI, recommendationAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { FiArrowLeft, FiShoppingBag, FiStar } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';



const GENDER_BADGE = {
  female: { label: 'Women', bg: '#FFF0F6', color: '#C2185B' },
  male:   { label: 'Men',   bg: '#E3F2FD', color: '#1565C0' },
  unisex: { label: 'Unisex', bg: '#F3E5F5', color: '#6A1B9A' },
};

const OCCASION_ICON = {
  casual: '👕', formal: '💼', party: '🎉', work: '🏢', gym: '🏋', date: '❤️',
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

const OutfitDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [outfit, setOutfit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [similarOutfits, setSimilarOutfits] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(true);
  const [failedImages, setFailedImages] = useState(new Set());
  const [shopOpen, setShopOpen] = useState(false);

  const handleImageError = (id) => {
    setFailedImages((prev) => new Set(prev).add(id));
  };


  useEffect(() => {
    const fetchOutfit = async () => {
      try {
        const res = await outfitAPI.getOutfit(id);
        setOutfit(res.data.outfit);
      } catch (err) {
        setError('Could not load outfit details.');
      } finally {
        setLoading(false);
      }
    };
    
    const fetchSimilar = async () => {
      try {
        setLoadingSimilar(true);
        const res = await recommendationAPI.getSimilar(id);
        setSimilarOutfits(res.data.similar || []);
      } catch (err) {
        console.error('Error fetching similar outfits:', err);
      } finally {
        setLoadingSimilar(false);
      }
    };

    fetchOutfit();
    fetchSimilar();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <HiOutlineSparkles className="text-6xl text-amber-500 animate-pulse" />
      </div>
    );
  }

  if (error || !outfit) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500 text-lg">{error || 'Outfit not found.'}</p>
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-amber-600 font-medium hover:underline">
          <FiArrowLeft /> Go Back
        </button>
      </div>
    );
  }

  const genderKey = (outfit.gender || 'unisex').toLowerCase();
  const badge = GENDER_BADGE[genderKey] || GENDER_BADGE.unisex;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Navigation */}
      <div className="bg-white border-b border-gray-200 px-3 sm:px-4 md:px-6 py-3 sm:py-4">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors font-medium text-xs sm:text-sm"
        >
          <FiArrowLeft /> Back to Recommendations
        </button>
      </div>

      <div className="container mx-auto px-3 sm:px-4 md:px-6 py-6 sm:py-8 md:py-10 max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="bg-white border border-gray-200 shadow-sm overflow-hidden"
        >
          <div className="grid grid-cols-1 md:grid-cols-2">
            {/* Left — Image */}
            <div className="relative h-64 sm:h-80 md:h-auto bg-gray-100 min-h-64 sm:min-h-80 md:min-h-96">
              {outfit.image_url ? (
                <img
                  src={outfit.image_url}
                  alt={outfit.name}
                  className="w-full h-full object-cover"
                  onError={(e) => { 
                    e.target.onerror = null; 
                    e.target.style.display = 'none';
                    e.target.parentNode.innerHTML = '<div class="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-400"><svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="4em" width="4em" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg><p class="mt-2 text-sm font-medium">Image unavailable</p></div>';
                  }}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                  <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height="4em" width="4em" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                  <p className="mt-2 text-sm font-medium">Image unavailable</p>
                </div>
              )}
              {outfit.is_trending && (
                <div className="absolute top-3 sm:top-4 left-3 sm:left-4 bg-amber-600 text-white px-2 sm:px-3 py-0.5 sm:py-1 text-xs font-bold tracking-widest uppercase">
                  Trending
                </div>
              )}
            </div>

            {/* Right — Details */}
            <div className="p-4 sm:p-6 md:p-8 flex flex-col gap-4 sm:gap-5">
              {/* Title + Badge */}
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded-full tracking-wide uppercase"
                    style={{ background: badge.bg, color: badge.color }}
                  >
                    {badge.label}
                  </span>
                  {outfit.occasion && (
                    <span className="text-xs px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full capitalize font-medium">
                      {OCCASION_ICON[outfit.occasion] || ''} {outfit.occasion}
                    </span>
                  )}
                  {outfit.season && outfit.season !== 'all' && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-full capitalize font-medium">
                      {outfit.season}
                    </span>
                  )}
                </div>
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 tracking-tight leading-snug">{outfit.name}</h1>
                {outfit.style_type && (
                  <p className="text-xs sm:text-sm text-gray-500 mt-1 capitalize tracking-wide">{outfit.style_type}</p>
                )}

                {/* Product Meta (Brand, Price) */}
                <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
                  {outfit.brand && (
                    <span className="text-sm font-bold text-gray-800 uppercase tracking-widest">
                      {outfit.brand}
                    </span>
                  )}
                  {outfit.price && (
                    <span className="text-xl font-bold text-amber-600">
                      {new Intl.NumberFormat('en-IN', { style: 'currency', currency: outfit.currency || 'INR' }).format(outfit.price)}
                    </span>
                  )}
                </div>
              </div>

              {/* Description */}
              {outfit.description && (
                <p className="text-sm sm:text-base text-gray-600 font-light leading-relaxed border-l-4 border-amber-500 pl-3 sm:pl-4">
                  {outfit.description}
                </p>
              )}

              {/* Dress Structure */}
              <div className="bg-gray-50 border border-gray-100 p-4 sm:p-5">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 sm:mb-4">Outfit Breakdown</p>
                <div className="grid grid-cols-1 gap-2 sm:gap-3">
                  {outfit.top && (
                    <div className="flex gap-2 sm:gap-3 items-start">
                      <span className="text-xs font-bold text-amber-600 uppercase tracking-widest w-16 sm:w-20 flex-shrink-0 pt-0.5">Top</span>
                      <span className="text-sm text-gray-800">{outfit.top}</span>
                    </div>
                  )}
                  {outfit.bottom && (
                    <div className="flex gap-2 sm:gap-3 items-start">
                      <span className="text-xs font-bold text-amber-600 uppercase tracking-widest w-16 sm:w-20 flex-shrink-0 pt-0.5">Bottom</span>
                      <span className="text-sm text-gray-800">{outfit.bottom}</span>
                    </div>
                  )}
                  {outfit.shoes && (
                    <div className="flex gap-2 sm:gap-3 items-start">
                      <span className="text-xs font-bold text-amber-600 uppercase tracking-widest w-16 sm:w-20 flex-shrink-0 pt-0.5">Shoes</span>
                      <span className="text-sm text-gray-800">{outfit.shoes}</span>
                    </div>
                  )}
                  {outfit.accessories?.length > 0 && (
                    <div className="flex gap-2 sm:gap-3 items-start">
                      <span className="text-xs font-bold text-amber-600 uppercase tracking-widest w-16 sm:w-20 flex-shrink-0 pt-0.5">Accessories</span>
                      <span className="text-sm text-gray-800">{outfit.accessories.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Colors */}
              {outfit.colors?.length > 0 && (
                <div>
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Color Palette</p>
                  <div className="flex flex-wrap gap-2">
                    {outfit.colors.map((color, i) => (
                      <span key={i} className="text-xs px-2 sm:px-3 py-1 sm:py-1.5 bg-gray-100 text-gray-700 font-medium tracking-wide uppercase border border-gray-200">
                        {color}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Fabric & Comfort */}
              {(outfit.fabric_types?.length > 0 || outfit.comfort_score != null) && (
                <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4">
                  {outfit.fabric_types?.length > 0 && (
                    <div>
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Fabrics</p>
                      <p className="text-sm text-gray-700">{outfit.fabric_types.join(', ')}</p>
                    </div>
                  )}
                  {outfit.comfort_score != null && (
                    <div>
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Comfort</p>
                      <div className="flex items-center gap-1">
                        <FiStar className="text-amber-500 text-sm" />
                        <span className="text-sm font-semibold text-gray-800">{(outfit.comfort_score * 10).toFixed(1)}/10</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Shop Links */}
              <div className="mt-2">
                {(!outfit.in_stock) ? (
                  <button disabled className="w-full bg-gray-200 text-gray-500 py-3 font-bold text-sm tracking-widest uppercase flex items-center justify-center gap-2 cursor-not-allowed">
                    <FiShoppingBag />
                    <span>Out of Stock</span>
                  </button>
                ) : outfit.shopping_links && Object.keys(outfit.shopping_links).length > 0 ? (
                  <div>
                    <button
                      onClick={() => setShopOpen(!shopOpen)}
                      className="w-full bg-amber-600 text-white py-3 font-bold text-sm tracking-widest uppercase hover:bg-amber-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <FiShoppingBag />
                      <span>{shopOpen ? 'Hide Links' : 'Shop Now'}</span>
                    </button>
                    {shopOpen && (
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
                ) : null}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Similar Recommendations Section */}
        <div className="mt-12 sm:mt-16 border-t border-gray-200 pt-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6 sm:mb-8 text-center uppercase tracking-widest">
            Similar Dresses
          </h2>
          
          {loadingSimilar ? (
            <div className="flex justify-center items-center py-12">
              <HiOutlineSparkles className="text-3xl text-amber-500 animate-pulse" />
            </div>
          ) : similarOutfits.filter(o => !failedImages.has(o.id)).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
              <AnimatePresence>
                {similarOutfits.filter(o => !failedImages.has(o.id)).map((item, idx) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="bg-white border border-gray-100 hover:border-gray-300 transition-colors cursor-pointer group flex flex-col"
                    onClick={() => navigate(`/outfits/${item.id}`)}
                  >
                    <div className="relative aspect-[3/4] bg-gray-100 overflow-hidden">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          onError={() => handleImageError(item.id)}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400">
                          No Image
                        </div>
                      )}
                    </div>
                    <div className="p-3 sm:p-4 flex-grow flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs sm:text-sm font-bold text-gray-900 line-clamp-2 leading-snug">
                          {item.name}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest">{item.brand || 'Unknown'}</p>
                      </div>
                      {item.price && (
                        <div className="mt-2 text-sm font-bold text-amber-600">
                          {new Intl.NumberFormat('en-IN', { style: 'currency', currency: item.currency || 'INR' }).format(item.price)}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="text-center py-10 bg-gray-50 border border-dashed border-gray-200">
              <p className="text-gray-500 text-sm">No similar items found right now.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OutfitDetail;

