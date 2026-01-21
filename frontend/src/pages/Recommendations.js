import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationAPI } from '../services/api';

const Recommendations = () => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    occasion: 'casual',
    season: 'all',
    limit: 10,
  });

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const generateRecommendations = async () => {
    setLoading(true);
    try {
      const response = await recommendationAPI.generate(filters);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error generating recommendations:', error);
      alert('Please complete your profile first!');
      navigate('/profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">✨ Personalized Recommendations</h1>

      {/* Filters */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold mb-4">Customize Your Recommendations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Occasion
            </label>
            <select
              name="occasion"
              value={filters.occasion}
              onChange={handleFilterChange}
              className="input-field"
            >
              <option value="all">All Occasions</option>
              <option value="casual">Casual</option>
              <option value="formal">Formal</option>
              <option value="party">Party</option>
              <option value="work">Work</option>
              <option value="gym">Gym</option>
              <option value="date">Date</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Season
            </label>
            <select
              name="season"
              value={filters.season}
              onChange={handleFilterChange}
              className="input-field"
            >
              <option value="all">All Seasons</option>
              <option value="summer">Summer</option>
              <option value="winter">Winter</option>
              <option value="spring">Spring</option>
              <option value="fall">Fall</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Number of Results
            </label>
            <select
              name="limit"
              value={filters.limit}
              onChange={handleFilterChange}
              className="input-field"
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="15">15</option>
              <option value="20">20</option>
            </select>
          </div>
        </div>
        <button
          onClick={generateRecommendations}
          className="btn-primary w-full"
          disabled={loading}
        >
          {loading ? 'Generating...' : '🎯 Generate Recommendations'}
        </button>
      </div>

      {/* Results */}
      {recommendations.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4">
            Your Top {recommendations.length} Matches
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((rec, index) => (
              <div key={index} className="card hover:transform hover:scale-105 transition">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-3xl font-bold text-purple-600">#{index + 1}</span>
                  <span className="text-2xl font-bold text-green-600">
                    {(rec.overall_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="bg-gray-200 h-48 rounded-lg mb-4 flex items-center justify-center">
                  {rec.outfit?.image_url ? (
                    <img
                      src={rec.outfit.image_url}
                      alt={rec.outfit.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    <span className="text-6xl">👗</span>
                  )}
                </div>

                <h3 className="text-xl font-bold mb-2">{rec.outfit?.name}</h3>
                <p className="text-gray-600 text-sm mb-4">
                  {rec.outfit?.description}
                </p>

                {/* Score Breakdown */}
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span>Style Match:</span>
                    <span>{(rec.scores.style_match * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Comfort:</span>
                    <span>{(rec.scores.comfort * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Trend:</span>
                    <span>{(rec.scores.trend * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Body Type:</span>
                    <span>{(rec.scores.body_type * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="flex gap-2 mb-4">
                  {rec.outfit?.colors?.slice(0, 3).map((color, i) => (
                    <span key={i} className="badge badge-info">
                      {color}
                    </span>
                  ))}
                </div>

                <button
                  onClick={() => navigate(`/outfit/${rec.outfit?.id}`)}
                  className="btn-secondary w-full"
                >
                  View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendations.length === 0 && !loading && (
        <div className="card text-center py-12">
          <span className="text-6xl mb-4 block">🎨</span>
          <h3 className="text-2xl font-bold mb-2">No Recommendations Yet</h3>
          <p className="text-gray-600 mb-4">
            Set your preferences above and click generate to get personalized outfit
            recommendations!
          </p>
        </div>
      )}
    </div>
  );
};

export default Recommendations;
