from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "API de la Mesa de Ayuda funcionando correctamente"
    }), 200