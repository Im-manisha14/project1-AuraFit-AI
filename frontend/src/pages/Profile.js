import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { userAPI } from '../services/api';
import axios from 'axios';

const Profile = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  const [profile, setProfile] = useState({
    height: '',
    weight: '',
    body_type: '',
    age: '',
    gender: '',
    skin_tone: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      const profileRes = await userAPI.getProfile().catch(() => ({ data: { profile: {} } }));

      if (profileRes.data.profile) {
        setProfile(profileRes.data.profile);
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

  const handleSave = async () => {
    setSaving(true);
    setMessage('');

    try {
      await userAPI.updateProfile(profile);
      setMessage('Profile updated successfully! ✅');
      // Redirect to recommendations page after 1 second
      setTimeout(() => {
        navigate('/recommendations');
      }, 1000);
    } catch (error) {
      setMessage('Error updating profile. Please try again. ❌');
      setSaving(false);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'user',
          width: { ideal: 1920, min: 640 },  // Higher resolution
          height: { ideal: 1080, min: 480 },
          frameRate: { ideal: 30 }  // Better frame rate
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        
        // Wait for video to be ready
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
        };
      }
      
      setShowCamera(true);
      setMessage('📸 Position the back of your hand facing the camera in good lighting');
    } catch (error) {
      setMessage('❌ Camera access denied. Please enable camera permissions.');
      console.error('Camera error:', error);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setShowCamera(false);
    setDetectionResult(null);
  };

  const captureAndDetect = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    // Check if video is ready
    const video = videoRef.current;
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
      setMessage('⏳ Camera is loading... Please wait a moment.');
      return;
    }
    
    setDetecting(true);
    setMessage('🔍 Analyzing hand skin tone...');

    try {
      const canvas = canvasRef.current;
      
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      
      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert to base64 with high quality
      const imageData = canvas.toDataURL('image/jpeg', 0.98);  // Higher quality
      
      console.log('Captured image size:', imageData.length, 'Canvas size:', canvas.width, 'x', canvas.height);
      
      // Send to backend
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        'http://localhost:5000/api/ai/detect-skin-tone',
        { image: imageData },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        const result = response.data;
        
        // Update profile with detected skin tone
        setProfile({
          ...profile,
          skin_tone: result.skin_tone,
        });
        
        setDetectionResult(result);
        setMessage(`✅ Skin tone detected: ${result.skin_tone}!`);
        
        // Stop camera after successful detection
        setTimeout(() => {
          stopCamera();
        }, 2000);
      } else {
        setMessage(`❌ ${response.data.error}`);
      }
    } catch (error) {
      console.error('Detection error:', error);
      let errorMsg = 'Detection failed. Please try again.';
      
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.message.includes('Network')) {
        errorMsg = 'Network error. Please check your connection.';
      } else if (error.message.includes('timeout')) {
        errorMsg = 'Request timed out. Please try with better lighting.';
      }
      
      setMessage(`❌ ${errorMsg}`);
    } finally {
      setDetecting(false);
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
            <div className="flex gap-2">
              <input
                type="text"
                name="skin_tone"
                value={profile.skin_tone || ''}
                onChange={handleProfileChange}
                className="input-field flex-1"
                placeholder="Fair, Light, Medium, Olive, Deep"
                readOnly
              />
              <button
                type="button"
                onClick={showCamera ? stopCamera : startCamera}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors whitespace-nowrap"
              >
                {showCamera ? '❌ Close' : '� Analyze Tone'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Use AI to detect your skin tone from your hand
            </p>
          </div>
        </div>

        {/* Camera Modal */}
        {showCamera && (
          <div className="mt-6 p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border-2 border-purple-300 shadow-lg">
            <h3 className="text-xl font-bold mb-2 text-center text-purple-800">
              ✋ Hand Skin Tone Detection
            </h3>
            <p className="text-sm text-gray-700 text-center mb-4">
              For best results:
            </p>
            <ul className="text-xs text-gray-600 mb-4 space-y-1 max-w-md mx-auto">
              <li>✓ Use natural daylight or bright white light</li>
              <li>✓ Show the BACK of your hand facing the camera</li>
              <li>✓ Keep your hand steady and fill the guide frame</li>
              <li>✓ Avoid shadows on your hand</li>
              <li>✓ Ensure your hand fills at least 30% of the frame</li>
            </ul>
            
            <div className="relative max-w-md mx-auto">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full rounded-lg border-4 border-purple-400 shadow-md bg-black"
                style={{ minHeight: '300px' }}
              />
              
              {/* Enhanced hand guide overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-56 h-64 border-4 border-dashed border-white rounded-xl flex items-center justify-center bg-black bg-opacity-20">
                  <div className="text-center">
                    <div className="text-6xl mb-2">🤚</div>
                    <span className="text-white text-sm font-semibold bg-black bg-opacity-60 px-3 py-2 rounded-lg">
                      Center back of hand here
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <canvas ref={canvasRef} className="hidden" />

            <div className="flex gap-3 mt-4 justify-center">
              <button
                type="button"
                onClick={captureAndDetect}
                disabled={detecting}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 font-medium"
              >
                {detecting ? '🔍 Analyzing...' : '✨ Detect Skin Tone'}
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                Cancel
              </button>
            </div>

            {/* Detection Result */}
            {detectionResult && (
              <div className="mt-4 p-4 bg-white rounded-lg border border-green-200">
                <h4 className="font-bold text-green-700 mb-2">
                  ✅ Detection Successful!
                </h4>
                <div className="space-y-2 text-sm">
                  <p>
                    <strong>Skin Tone:</strong> {detectionResult.skin_tone}
                  </p>
                  <p>
                    <strong>Brightness:</strong> {detectionResult.brightness}
                  </p>
                  <div>
                    <strong>Recommended Colors:</strong>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {detectionResult.recommended_colors?.map((color, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                        >
                          {color}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
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
