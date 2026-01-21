import React, { useState, useEffect } from 'react';
import { userAPI } from '../services/api';

const Profile = () => {
  const [profile, setProfile] = useState({
    height: '',
    weight: '',
    body_type: '',
    age: '',
    gender: '',
    skin_tone: '',
  });
  const [preferences, setPreferences] = useState({
    preferred_colors: [],
    preferred_styles: [],
    avoided_patterns: [],
    comfort_level: 'medium',
    preferred_occasions: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      const [profileRes, prefsRes] = await Promise.all([
        userAPI.getProfile().catch(() => ({ data: { profile: {} } })),
        userAPI.getPreferences().catch(() => ({ data: { preferences: {} } })),
      ]);

      if (profileRes.data.profile) {
        setProfile(profileRes.data.profile);
      }
      if (prefsRes.data.preferences) {
        setPreferences(prefsRes.data.preferences);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileChange = (e) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value,
    });
  };

  const handlePreferenceChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('_')) {
      // Handle array fields
      const values = value.split(',').map((v) => v.trim());
      setPreferences({
        ...preferences,
        [name]: values,
      });
    } else {
      setPreferences({
        ...preferences,
        [name]: value,
      });
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');

    try {
      await Promise.all([
        userAPI.updateProfile(profile),
        userAPI.updatePreferences(preferences),
      ]);
      setMessage('Profile updated successfully! ✅');
    } catch (error) {
      setMessage('Error updating profile. Please try again. ❌');
    } finally {
      setSaving(false);
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
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Your Profile</h1>

      {message && (
        <div
          className={`mb-6 px-4 py-3 rounded ${
            message.includes('✅')
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {message}
        </div>
      )}

      {/* Body Profile */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold mb-4">📏 Body Profile</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Height (cm)
            </label>
            <input
              type="number"
              name="height"
              value={profile.height || ''}
              onChange={handleProfileChange}
              className="input-field"
              placeholder="170"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Weight (kg)
            </label>
            <input
              type="number"
              name="weight"
              value={profile.weight || ''}
              onChange={handleProfileChange}
              className="input-field"
              placeholder="65"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Body Type
            </label>
            <select
              name="body_type"
              value={profile.body_type || ''}
              onChange={handleProfileChange}
              className="input-field"
            >
              <option value="">Select Body Type</option>
              <option value="hourglass">Hourglass</option>
              <option value="pear">Pear</option>
              <option value="apple">Apple</option>
              <option value="rectangle">Rectangle</option>
              <option value="inverted_triangle">Inverted Triangle</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">Age</label>
            <input
              type="number"
              name="age"
              value={profile.age || ''}
              onChange={handleProfileChange}
              className="input-field"
              placeholder="25"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Gender
            </label>
            <select
              name="gender"
              value={profile.gender || ''}
              onChange={handleProfileChange}
              className="input-field"
            >
              <option value="">Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="prefer-not-to-say">Prefer not to say</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Skin Tone
            </label>
            <input
              type="text"
              name="skin_tone"
              value={profile.skin_tone || ''}
              onChange={handleProfileChange}
              className="input-field"
              placeholder="Fair, Medium, Dark"
            />
          </div>
        </div>
      </div>

      {/* Style Preferences */}
      <div className="card mb-8">
        <h2 className="text-2xl font-bold mb-4">🎨 Style Preferences</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Preferred Colors (comma-separated)
            </label>
            <input
              type="text"
              name="preferred_colors"
              value={preferences.preferred_colors?.join(', ') || ''}
              onChange={handlePreferenceChange}
              className="input-field"
              placeholder="blue, black, white, green"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Preferred Styles (comma-separated)
            </label>
            <input
              type="text"
              name="preferred_styles"
              value={preferences.preferred_styles?.join(', ') || ''}
              onChange={handlePreferenceChange}
              className="input-field"
              placeholder="casual, formal, sporty, bohemian"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Avoided Patterns (comma-separated)
            </label>
            <input
              type="text"
              name="avoided_patterns"
              value={preferences.avoided_patterns?.join(', ') || ''}
              onChange={handlePreferenceChange}
              className="input-field"
              placeholder="stripes, polka-dots"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Comfort Level
            </label>
            <select
              name="comfort_level"
              value={preferences.comfort_level || 'medium'}
              onChange={handlePreferenceChange}
              className="input-field"
            >
              <option value="low">Low (Style over comfort)</option>
              <option value="medium">Medium (Balanced)</option>
              <option value="high">High (Comfort first)</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Preferred Occasions (comma-separated)
            </label>
            <input
              type="text"
              name="preferred_occasions"
              value={preferences.preferred_occasions?.join(', ') || ''}
              onChange={handlePreferenceChange}
              className="input-field"
              placeholder="work, party, casual, gym, date"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="btn-primary"
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
};

export default Profile;
