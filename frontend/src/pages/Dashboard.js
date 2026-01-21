import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { outfitAPI, recommendationAPI } from '../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [trending, setTrending] = useState([]);
  const [recentRecommendations, setRecentRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [trendingRes, recsRes] = await Promise.all([
        outfitAPI.getTrending(6),
        recommendationAPI.getHistory({ per_page: 6 }),
      ]);
      
      setTrending(trendingRes.data.outfits || []);
      setRecentRecommendations(recsRes.data.recommendations || []);
    } catch (error) {
      console.error('Error loading dashboard:', error);
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
      {/* Welcome Section */}
      <div className="card mb-8 gradient-bg text-white">
        <h1 className="text-4xl font-bold mb-2">Welcome back, {user?.username}! 👋</h1>
        <p className="text-lg opacity-90">
          Discover your perfect style with AI-powered recommendations
        </p>
        <button
          onClick={() => navigate('/recommendations')}
          className="mt-4 bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-purple-100 transition"
        >
          Get New Recommendations
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card bg-gradient-to-br from-purple-500 to-pink-500 text-white">
          <h3 className="text-lg font-semibold mb-2">Total Recommendations</h3>
          <p className="text-4xl font-bold">{recentRecommendations.length}</p>
        </div>
        <div className="card bg-gradient-to-br from-blue-500 to-cyan-500 text-white">
          <h3 className="text-lg font-semibold mb-2">Trending Styles</h3>
          <p className="text-4xl font-bold">{trending.length}</p>
        </div>
        <div className="card bg-gradient-to-br from-green-500 to-teal-500 text-white">
          <h3 className="text-lg font-semibold mb-2">Profile Complete</h3>
          <p className="text-4xl font-bold">80%</p>
        </div>
      </div>

      {/* Trending Outfits */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">🔥 Trending Now</h2>
          <button
            onClick={() => navigate('/trends')}
            className="text-purple-600 font-semibold hover:text-purple-800"
          >
            View All →
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trending.map((outfit) => (
            <div
              key={outfit.id}
              className="card cursor-pointer hover:transform hover:scale-105 transition"
              onClick={() => navigate(`/outfit/${outfit.id}`)}
            >
              <div className="bg-gray-200 h-48 rounded-lg mb-4 flex items-center justify-center">
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
              <p className="text-gray-600 text-sm mb-2">{outfit.style_type}</p>
              <div className="flex items-center justify-between">
                <span className="badge badge-info">{outfit.occasion}</span>
                <span className="text-yellow-500">⭐ {outfit.trend_score?.toFixed(1)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Recommendations */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">💡 Recent Recommendations</h2>
          <button
            onClick={() => navigate('/recommendations')}
            className="text-purple-600 font-semibold hover:text-purple-800"
          >
            View All →
          </button>
        </div>
        {recentRecommendations.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-xl text-gray-600 mb-4">
              No recommendations yet! Let's create your first one.
            </p>
            <button
              onClick={() => navigate('/recommendations')}
              className="btn-primary"
            >
              Generate Recommendations
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recentRecommendations.map((rec) => (
              <div key={rec.id} className="card">
                <div className="mb-4">
                  <h3 className="text-xl font-bold mb-2">{rec.outfit?.name}</h3>
                  <p className="text-gray-600 text-sm">{rec.outfit?.description}</p>
                </div>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span>Overall Score:</span>
                    <span className="font-bold">{(rec.overall_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                      style={{ width: `${rec.overall_score * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <span className="badge badge-success">{rec.occasion}</span>
                  <span className="badge badge-warning">{rec.season}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
