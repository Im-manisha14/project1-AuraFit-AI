import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { userAPI } from '../services/api';

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
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [manualColor, setManualColor] = useState('#B89685'); // Default skin color
  const [detecting, setDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  useEffect(() => {
    if (showCamera) {
      const timer = setTimeout(() => {
        startCamera();
      }, 50);
      return () => {
        clearTimeout(timer);
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };
    }
  }, [showCamera]);

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

  const COLOR_MAP = {
    'lavender': '#E6E6FA', 'pastel blue': '#AEC6CF', 'soft pink': '#FFB6C1',
    'peach': '#FFDAB9', 'beige': '#F5F5DC', 'mint green': '#98FF98',
    'emerald': '#50C878', 'teal': '#008080', 'mustard': '#FFDB58',
    'earth tones': '#8B6914', 'maroon': '#800000', 'cream': '#FFFDD0',
    'royal blue': '#4169E1', 'yellow': '#FFD700', 'white': '#F5F5F5',
    'navy': '#1B2A6B', 'forest green': '#228B22',
  };

  const getBodyTypeOptions = (gender) => {
    if (gender === 'male') return [
      { value: 'athletic', label: 'Athletic' },
      { value: 'slim', label: 'Slim' },
      { value: 'average', label: 'Average' },
      { value: 'muscular', label: 'Muscular' },
      { value: 'heavy', label: 'Heavy' },
    ];
    if (gender === 'female') return [
      { value: 'hourglass', label: 'Hourglass' },
      { value: 'pear', label: 'Pear' },
      { value: 'apple', label: 'Apple' },
      { value: 'rectangle', label: 'Rectangle' },
      { value: 'inverted_triangle', label: 'Inverted Triangle' },
    ];
    return [];
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    const updated = { ...profile, [name]: value };
    if (name === 'gender') {
      const validOptions = getBodyTypeOptions(value).map(o => o.value);
      if (validOptions.length > 0 && !validOptions.includes(updated.body_type)) {
        updated.body_type = '';
      }
    }
    setProfile(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');

    try {
      await userAPI.updateProfile(profile);
      setMessage('Profile updated successfully! ✅');
      // Redirect to recommendations page after 1 second
      setTimeout(() => {
        navigate('/recommendations', { state: { autoGenerate: true } });
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
      
      setMessage('📸 Position the back of your hand facing the camera in good lighting');
    } catch (error) {
      setMessage('❌ Camera access denied or unavailable. Please check permissions.');
      console.error('Camera error:', error);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
    setDetectionResult(null);
    setCapturedImage(null);
  };
  
  const retakePhoto = () => {
    setDetectionResult(null);
    setCapturedImage(null);
    startCamera();
  };

  const detectFromManualColor = async () => {
    setDetecting(true);
    setMessage('🎨 Analyzing selected color...');

    try {
      // Convert hex to RGB
      const hex = manualColor.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);

      const response = await api.post(
        '/ai/detect-skin-tone',
        { rgb: [r, g, b] }
      );

      if (response.data.success) {
        const result = response.data;
        
        setProfile({
          ...profile,
          skin_tone: result.skin_tone,
        });
        
        setDetectionResult(result);
        setMessage(`✅ Skin tone detected: ${result.skin_tone}!`);
        
        setTimeout(() => {
          setShowColorPicker(false);
        }, 2000);
      } else {
        setMessage(`❌ ${response.data.error}`);
      }
    } catch (error) {
      console.error('Manual detection error:', error);
      const errorMsg = error.response?.data?.error || 'Detection failed. Please try again.';
      setMessage(`❌ ${errorMsg}`);
    } finally {
      setDetecting(false);
    }
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
      const videoWidth = video.videoWidth || 640;
      const videoHeight = video.videoHeight || 480;
      
      // CROP ONLY CENTER REGION (where hand is placed in guide box)
      // Guide box is: 25%-75% horizontally, 20%-80% vertically
      const cropX = Math.floor(videoWidth * 0.25);
      const cropY = Math.floor(videoHeight * 0.20);
      const cropWidth = Math.floor(videoWidth * 0.50);  // 25% to 75%
      const cropHeight = Math.floor(videoHeight * 0.60); // 20% to 80%
      
      // Set canvas size to cropped region
      canvas.width = cropWidth;
      canvas.height = cropHeight;
      
      // Draw ONLY the cropped region (removes background noise)
      const context = canvas.getContext('2d');
      context.drawImage(video, cropX, cropY, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);
      
      // Convert to base64 with high quality
      const imageData = canvas.toDataURL('image/jpeg', 0.98);
      setCapturedImage(imageData);
      
      console.log('Cropped image size:', cropWidth, 'x', cropHeight, 'Original:', videoWidth, 'x', videoHeight);
      
      // Stop the live feed since we captured
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      // Send to backend
      const response = await api.post(
        '/ai/detect-skin-tone',
        { image: imageData }
      );

      if (response.data.success) {
        const result = response.data;
        
        setDetectionResult(result);
        setMessage(`✅ Skin tone detected!`);
      } else {
        setMessage(`❌ ${response.data.error || response.data.message}`);
        setCapturedImage(null); // Clear on fail so they can see camera
        startCamera(); // restart camera
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
      setCapturedImage(null);
      startCamera(); // restart camera on error
    } finally {
      setDetecting(false);
    }
  };
  
  const acceptDetection = () => {
    if (detectionResult) {
      setProfile({
        ...profile,
        skin_tone: detectionResult.skin_tone,
      });
      stopCamera();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 sm:h-16 sm:w-16 border-t-4 border-b-4 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm sm:text-base">Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8 max-w-4xl">
      <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4 sm:mb-6 lg:mb-8 text-center sm:text-left">Your Profile</h1>

      {message && (
        <div
          className={`mb-4 sm:mb-6 px-3 sm:px-4 py-2 sm:py-3 rounded text-sm sm:text-base ${
            message.includes('✅')
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {message}
        </div>
      )}

      {/* Body Profile */}
      <div className="card mb-6 sm:mb-8 p-4 sm:p-6">
        <h2 className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4">📏 Body Profile</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 lg:gap-6">
          <div>
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
              Height (cm)
            </label>
            <input
              type="number"
              name="height"
              value={profile.height || ''}
              onChange={handleProfileChange}
              className="input-field w-full text-sm sm:text-base"
              placeholder="170"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
              Weight (kg)
            </label>
            <input
              type="number"
              name="weight"
              value={profile.weight || ''}
              onChange={handleProfileChange}
              className="input-field w-full text-sm sm:text-base"
              placeholder="65"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">Age</label>
            <input
              type="number"
              name="age"
              value={profile.age || ''}
              onChange={handleProfileChange}
              className="input-field w-full text-sm sm:text-base"
              placeholder="25"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
              Gender
            </label>
            <select
              name="gender"
              value={profile.gender || ''}
              onChange={handleProfileChange}
              className="input-field w-full text-sm sm:text-base"
            >
              <option value="">Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="prefer-not-to-say">Prefer not to say</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
              Body Type
            </label>
            <select
              name="body_type"
              value={profile.body_type || ''}
              onChange={handleProfileChange}
              className="input-field w-full text-sm sm:text-base"
              disabled={!profile.gender || getBodyTypeOptions(profile.gender).length === 0}
            >
              <option value="">
                {!profile.gender ? 'Select gender first' : 'Select Body Type'}
              </option>
              {getBodyTypeOptions(profile.gender).map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            {!profile.gender && (
              <p className="text-xs text-amber-600 mt-1">⚠ Select your gender first to see body type options</p>
            )}
          </div>
          <div className="col-span-1 sm:col-span-2">
            <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
              Skin Tone
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                name="skin_tone"
                value={profile.skin_tone || ''}
                onChange={handleProfileChange}
                className="input-field flex-1 text-sm sm:text-base"
                placeholder="Fair, Light, Medium, Olive, Deep"
                readOnly
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowCamera(true)}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 sm:py-3 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors whitespace-nowrap text-xs sm:text-sm font-medium"
                >
                  📷 Camera
                </button>
                <button
                  type="button"
                  onClick={() => setShowColorPicker(true)}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 sm:py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors whitespace-nowrap text-xs sm:text-sm font-medium"
                >
                  🎨 Color
                </button>
              </div>
            </div>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              Use AI to detect your skin tone from your hand
            </p>
          </div>
        </div>

        {/* Camera Modal */}
        {showCamera && (
          <div className="mt-4 sm:mt-6 p-3 sm:p-4 lg:p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border-2 border-purple-300 shadow-lg">
            <h3 className="text-lg sm:text-xl font-bold mb-2 text-center text-purple-800">
              ✋ Hand Skin Tone Detection
            </h3>
            <p className="text-xs sm:text-sm text-gray-700 text-center mb-3 sm:mb-4">
              For best results:
            </p>
            <ul className="text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 space-y-1 max-w-sm sm:max-w-md mx-auto px-2 sm:px-0">
              <li>✓ Use natural daylight or bright white light</li>
              <li>✓ Show the BACK of your hand facing the camera</li>
              <li>✓ Keep your hand steady and fill the guide frame</li>
              <li>✓ Avoid shadows on your hand</li>
              <li>✓ Ensure your hand fills at least 30% of the frame</li>
            </ul>
            
            <div className="relative max-w-xs sm:max-w-sm lg:max-w-md mx-auto aspect-video bg-black rounded-lg overflow-hidden border-2 sm:border-4 border-purple-400 shadow-md">
              {!capturedImage ? (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }}
                  />
                  {/* Transparent dashed guide */}
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-[50%] h-[60%] border-2 border-dashed border-white rounded-lg flex items-end justify-center pb-2 bg-black bg-opacity-0 shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]">
                      <span className="text-white text-xs sm:text-sm font-semibold bg-black bg-opacity-50 px-2 py-1 rounded">
                        HAND HERE
                      </span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900">
                  <img src={capturedImage} alt="Captured hand" className="h-[60%] w-auto rounded-lg object-cover border-2 border-purple-500 mb-2 shadow-lg" />
                  {detecting && <p className="text-white text-sm animate-pulse">Analyzing...</p>}
                </div>
              )}
            </div>

            <canvas ref={canvasRef} className="hidden" />

            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mt-3 sm:mt-4 justify-center">
              {!detectionResult ? (
                <>
                  <button
                    type="button"
                    onClick={captureAndDetect}
                    disabled={detecting}
                    className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 font-medium text-sm sm:text-base"
                  >
                    {detecting ? '🔍 Analyzing...' : '✨ Detect Skin Tone'}
                  </button>
                  <button
                    type="button"
                    onClick={stopCamera}
                    disabled={detecting}
                    className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium text-sm sm:text-base"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={acceptDetection}
                    className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm sm:text-base"
                  >
                    Use This Skin Tone
                  </button>
                  <button
                    type="button"
                    onClick={retakePhoto}
                    className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium text-sm sm:text-base"
                  >
                    Retake
                  </button>
                </>
              )}
            </div>

            {/* Detection Result Info Box */}
            {detectionResult && (
              <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-white rounded-lg border border-purple-200 shadow-sm">
                <h4 className="font-bold text-purple-700 mb-2 text-center text-sm sm:text-base">
                  ✓ Skin Tone Detected
                </h4>
                <div className="flex flex-col items-center justify-center space-y-3">
                  {detectionResult.rgb_value && (
                    <div
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-full border-4 border-white shadow-md"
                      style={{ backgroundColor: `rgb(${detectionResult.rgb_value.join(',')})` }}
                      title={`rgb(${detectionResult.rgb_value.join(', ')})`}
                    />
                  )}
                  <span className="text-xl font-bold text-gray-800">{detectionResult.skin_tone}</span>
                  <p className="text-xs sm:text-sm text-gray-500 text-center max-w-xs">
                    Your detected skin tone will be used for personalized outfit recommendations.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Manual Color Picker Modal */}
        {showColorPicker && (
          <div className="mt-4 sm:mt-6 p-3 sm:p-4 lg:p-6 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border-2 border-blue-300 shadow-lg">
            <h3 className="text-lg sm:text-xl font-bold mb-2 text-center text-blue-800">
              🎨 Manual Skin Tone Selection
            </h3>
            <p className="text-xs sm:text-sm text-gray-700 text-center mb-3 sm:mb-4">
              Select a color that closely matches your skin tone:
            </p>

            <div className="max-w-sm sm:max-w-md mx-auto">
              <div className="mb-3 sm:mb-4">
                <label className="block text-gray-700 font-semibold mb-2 text-sm sm:text-base">
                  Pick Your Skin Color:
                </label>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                  <input
                    type="color"
                    value={manualColor}
                    onChange={(e) => setManualColor(e.target.value)}
                    className="w-12 h-12 sm:w-16 sm:h-16 border-2 border-gray-300 rounded-lg cursor-pointer mx-auto sm:mx-0"
                  />
                  <div className="flex-1 w-full">
                    <input
                      type="text"
                      value={manualColor}
                      onChange={(e) => setManualColor(e.target.value)}
                      className="input-field w-full text-sm sm:text-base"
                      placeholder="#B89685"
                    />
                    <p className="text-xs sm:text-sm text-gray-500 mt-1">
                      Hex color code for your skin tone
                    </p>
                  </div>
                </div>
              </div>

              <div className="mb-3 sm:mb-4">
                <p className="text-xs sm:text-sm text-gray-600 mb-2">Common skin tones:</p>
                <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-1 sm:gap-2">
                  {[
                    { name: 'Very Fair', color: '#F7E7CE' },
                    { name: 'Fair', color: '#F3D5AB' },
                    { name: 'Light', color: '#E8C4A0' },
                    { name: 'Medium', color: '#D4A574' },
                    { name: 'Olive', color: '#C19A6B' },
                    { name: 'Deep', color: '#A0784A' },
                    { name: 'Very Deep', color: '#8B4513' }
                  ].map((preset) => (
                    <button
                      key={preset.name}
                      onClick={() => setManualColor(preset.color)}
                      className="flex items-center gap-1 px-2 py-1 border rounded text-xs hover:bg-gray-100 transition-colors"
                      style={{ borderColor: preset.color }}
                    >
                      <div
                        className="w-3 h-3 sm:w-4 sm:h-4 rounded border flex-shrink-0"
                        style={{ backgroundColor: preset.color }}
                      ></div>
                      <span className="truncate">{preset.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 justify-center">
                <button
                  type="button"
                  onClick={detectFromManualColor}
                  disabled={detecting}
                  className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 font-medium text-sm sm:text-base"
                >
                  {detecting ? '🔍 Analyzing...' : '✨ Analyze Color'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowColorPicker(false)}
                  className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium text-sm sm:text-base"
                >
                  Cancel
                </button>
              </div>

              {/* Detection Result for Manual Color */}
              {detectionResult && (
                <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="font-bold text-green-700 mb-2 text-sm sm:text-base">
                    ✅ Analysis Complete!
                  </h4>
                  <div className="space-y-2 text-xs sm:text-sm">
                    <div className="flex items-center gap-3">
                      <strong>Skin Tone:</strong>
                      {detectionResult.rgb_value && (
                        <div
                          className="w-8 h-8 rounded border-2 border-gray-300 shadow-sm flex-shrink-0"
                          style={{ backgroundColor: `rgb(${detectionResult.rgb_value.join(',')})` }}
                          title={`rgb(${detectionResult.rgb_value.join(', ')})`}
                        />
                      )}
                      <span>{detectionResult.skin_tone}</span>
                    </div>
                    <p>
                      <strong>RGB Values:</strong> {detectionResult.rgb_value?.join(', ')}
                    </p>
                    <div>
                      <strong>Recommended Colors:</strong>
                      <div className="flex flex-wrap gap-1 sm:gap-2 mt-1">
                        {detectionResult.recommended_colors?.map((color, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1"
                          >
                            <div
                              className="w-3 h-3 rounded-full border border-blue-300 flex-shrink-0"
                              style={{ backgroundColor: COLOR_MAP[color.toLowerCase()] || color }}
                            />
                            {color}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-center sm:justify-end mt-6 sm:mt-8">
        <button
          onClick={handleSave}
          className="w-full sm:w-auto btn-primary px-6 sm:px-8 py-3 text-sm sm:text-base font-semibold"
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
};

export default Profile;
