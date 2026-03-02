"""
API routes for AI-powered skin tone detection
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ml_models.hand_skin_detector import HandSkinToneDetector

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Initialize detector
detector = HandSkinToneDetector()

@bp.route('/detect-skin-tone', methods=['POST'])
@jwt_required()
def detect_skin_tone():
    """
    Detect skin tone from hand image
    
    Expects JSON with:
        - image: base64 encoded image string
        OR
        - rgb: [R, G, B] array for direct color input
    
    Returns:
        - skin_tone: Classification (Fair, Light, Medium, Olive, Deep)
        - rgb_value: Average RGB color
        - brightness: Brightness value
        - recommended_colors: List of recommended outfit colors
    """
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"[AI] Processing skin tone detection for user {user_id}")
        
        # Check if RGB values are provided directly
        if 'rgb' in data and isinstance(data['rgb'], list) and len(data['rgb']) == 3:
            print(f"[AI] Using direct RGB input: {data['rgb']}")
            result = detector.detect_from_rgb(data['rgb'])
        elif 'image' in data:
            print(f"[AI] Using camera image detection")
            result = detector.detect_skin_from_image(data['image'])
        else:
            return jsonify({'error': 'No image data or RGB values provided'}), 400
        
        if not result.get('success', False):
            print(f"[AI] Detection failed: {result.get('error')}")
            return jsonify(result), 400
        
        print(f"[AI] Detection successful: {result['skin_tone']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[AI] Error in skin tone detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@bp.route('/recommended-colors/<skin_tone>', methods=['GET'])
@jwt_required()
def get_recommended_colors(skin_tone):
    """
    Get recommended colors for a specific skin tone
    
    Args:
        skin_tone: fair, light, medium, olive, or deep
    
    Returns:
        List of recommended outfit colors
    """
    try:
        colors = detector.get_recommended_colors(skin_tone)
        
        if not colors:
            return jsonify({
                'error': 'Invalid skin tone category'
            }), 400
        
        return jsonify({
            'skin_tone': skin_tone.title(),
            'recommended_colors': colors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
