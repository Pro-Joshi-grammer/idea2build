from flask import Blueprint, jsonify, request
import razorpay
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

payment_bp = Blueprint('payment', __name__)

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@payment_bp.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        # Create a Razorpay Order for a test payment
        order_amount = 99900 # 999 INR (amount is in paise)
        order_currency = 'INR'
        order_receipt = f'receipt_{user_id}'
        
        razorpay_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': order_receipt,
            'notes': {
                'user_id': user_id
            }
        })
        
        return jsonify({
            'order_id': razorpay_order['id'],
            'amount': order_amount,
            'currency': order_currency,
            'key_id': RAZORPAY_KEY_ID
        })
    except Exception as e:
        print(f"Razorpay error: {e}")
        return jsonify(error=str(e)), 500
