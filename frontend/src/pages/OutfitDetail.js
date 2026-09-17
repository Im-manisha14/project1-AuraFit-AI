import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { outfitAPI } from '../services/api';
import { motion } from 'framer-motion';
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

const checkValidUrl = (url) => {
  if (!url) return false;
  const lower = url.toLowerCase();
  if (lower.includes('aurafit.store') || lower.includes('example.com') || lower.includes('placeholder')) return false;
  return true;
};

const OutfitDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [outfit, setOutfit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


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
    fetchOutfit();
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
                  onError={(e) => { e.target.onerror = null; e.target.src = `https://loremflickr.com/600/900/fashion,outfit?lock=${outfit.id}`; }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <HiOutlineSparkles className="text-6xl sm:text-8xl text-gray-300" />
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
                      ${outfit.price.toFixed(2)}
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
                ) : (!checkValidUrl(outfit.product_url)) ? (
                  <button disabled className="w-full bg-gray-100 text-gray-500 py-3 font-bold text-sm tracking-widest uppercase flex items-center justify-center gap-2 cursor-not-allowed border border-gray-200">
                    <FiShoppingBag />
                    <span>Shopping Link Unavailable</span>
                  </button>
                ) : (
                  <motion.a
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    href={outfit.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full bg-amber-600 text-white py-3 font-bold text-sm tracking-widest uppercase hover:bg-amber-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <FiShoppingBag />
                    <span>Shop Exact Item</span>
                  </motion.a>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default OutfitDetail;

