import React, { useState, useEffect } from 'react';
import { outfitAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

const Trends = () => {
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrending();
  }, []);

  const loadTrending = async () => {
    try {
      const response = await outfitAPI.getTrending(12);
      setTrending(response.data.outfits || []);
    } catch (error) {
      console.error('Error loading trends:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🔥 Fashion Trends 2026</h1>
        <p className="text-gray-600">
          Discover the hottest fashion trends and stay ahead of the curve
        </p>
      </div>

      {/* Current Trends Info */}
      <div className="card mb-8 gradient-bg text-white">
        <h2 className="text-2xl font-bold mb-4">What's Hot Right Now</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-2">🎨 Trending Colors</h3>
            <div className="flex flex-wrap gap-2">
              <span className="badge" style={{ background: '#8FBC8F' }}>
                Sage Green
              </span>
              <span className="badge" style={{ background: '#E6E6FA' }}>
                Lavender
              </span>
              <span className="badge" style={{ background: '#E07A5F' }}>
                Terracotta
              </span>
              <span className="badge" style={{ background: '#000080', color: '#fff' }}>
                Navy
              </span>
              <span className="badge" style={{ background: '#FFFDD0' }}>
                Cream
              </span>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-2">✨ Trending Styles</h3>
            <ul className="space-y-1">
              <li>• Oversized & Relaxed Fits</li>
              <li>• Minimalist Aesthetic</li>
              <li>• Sustainable Fashion</li>
              <li>• Vintage Revival</li>
              <li>• Athleisure Fusion</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Trending Outfits Grid */}
      <h2 className="text-2xl font-bold mb-4">Top Trending Outfits</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {trending.map((outfit, index) => (
          <div
            key={outfit.id}
            className="card cursor-pointer hover:transform hover:scale-105 transition"
            onClick={() => navigate(`/outfit/${outfit.id}`)}
          >
            <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-full font-bold text-sm z-10">
              #{index + 1}
            </div>
            <div className="bg-gray-200 h-56 rounded-lg mb-4 flex items-center justify-center">
              {outfit.image_url ? (
                <img
                  src={outfit.image_url}
                  alt={outfit.name}
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <span className="text-6xl">👗</span>
              )}
            </div>
            <h3 className="text-xl font-bold mb-2">{outfit.name}</h3>
            <p className="text-gray-600 text-sm mb-3 line-clamp-2">
              {outfit.description}
            </p>
            <div className="flex items-center justify-between mb-3">
              <span className="badge badge-info">{outfit.style_type}</span>
              <span className="text-yellow-500 font-semibold">
                ⭐ {outfit.trend_score?.toFixed(1)}
              </span>
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="badge badge-success">{outfit.occasion}</span>
              <span className="badge badge-warning">{outfit.season}</span>
            </div>
          </div>
        ))}
      </div>

      {trending.length === 0 && (
        <div className="card text-center py-12">
          <span className="text-6xl mb-4 block">📊</span>
          <h3 className="text-2xl font-bold mb-2">No Trending Data Available</h3>
          <p className="text-gray-600">
            Check back later for the latest fashion trends!
          </p>
        </div>
      )}
    </div>
  );
};

export default Trends;
