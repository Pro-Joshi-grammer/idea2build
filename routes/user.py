from flask import Blueprint, request, jsonify
from services.user import (
    get_or_create_user, get_user, update_user_profile,
    check_usage_limit, upgrade_to_premium, get_user_sessions
)
from services.session import get_session

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/user/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = get_or_create_user(user_id)
    return jsonify(user)

@user_bp.route('/api/user/<user_id>', methods=['PUT'])
def update_profile(user_id):
    data = request.json or {}
    updated = update_user_profile(user_id, {
        'display_name': data.get('display_name'),
        'bio': data.get('bio'),
        'avatar_color': data.get('avatar_color')
    })
    return jsonify(updated)

@user_bp.route('/api/user/<user_id>/usage', methods=['GET'])
def get_usage(user_id):
    info = check_usage_limit(user_id)
    return jsonify(info)

@user_bp.route('/api/user/<user_id>/upgrade', methods=['POST'])
def upgrade(user_id):
    """Mock payment endpoint - upgrades user to premium."""
    # In production this would verify a payment processor webhook/token
    user = upgrade_to_premium(user_id)
    return jsonify({
        'success': True,
        'plan': user.get('plan'),
        'message': 'Welcome to Premium! Unlimited API calls activated.'
    })

@user_bp.route('/api/user/<user_id>/sessions', methods=['GET'])
def list_sessions(user_id):
    sessions = get_user_sessions(user_id)
    return jsonify({'sessions': sessions})

@user_bp.route('/api/session/<session_id>', methods=['GET'])
def get_session_detail(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    # Return safe session data (messages + context + stage)
    return jsonify({
        'session_id': session.get('session_id'),
        'title': session.get('title', 'Untitled'),
        'messages': session.get('messages', []),
        'context': session.get('context', {}),
        'stage': session.get('stage', 'intake'),
        'artifacts_ready': session.get('artifacts_ready', False),
        'artifacts': session.get('artifacts', {})
    })
