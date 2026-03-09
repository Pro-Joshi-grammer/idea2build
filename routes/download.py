from flask import Blueprint, jsonify, send_file
from services.artifacts import generate_presigned_url
from services.scaffolder import generate_scaffold_zip

download_bp = Blueprint('download', __name__)

FILE_MAP = {
    "requirements": "requirements.md",
    "design": "design.md",
    "mvp-plan": "mvp-plan.md"
}

@download_bp.route('/api/download/<session_id>/<file_type>', methods=['GET'])
def download(session_id, file_type):
    filename = FILE_MAP.get(file_type)
    if not filename:
        return jsonify({"error": "Invalid file type"}), 400

    s3_key = f"{session_id}/{filename}"
    try:
        url = generate_presigned_url(s3_key)
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@download_bp.route('/api/download/<session_id>/scaffold', methods=['GET'])
def download_scaffold(session_id):
    try:
        zip_io = generate_scaffold_zip(session_id)
        return send_file(zip_io, mimetype='application/zip', as_attachment=True, download_name=f'{session_id}_starter.zip')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
