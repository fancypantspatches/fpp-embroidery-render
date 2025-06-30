import os
import io
import tempfile
import traceback  # <--- 1. ADD THIS LINE
from flask import Flask, request, send_file, jsonify
from pyembroidery import read

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "ok", "message": "Embroidery rendering service is running."})

@app.route('/render', methods=['POST'])
def render_embroidery_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.filename) as temp_f:
            uploaded_file.save(temp_f)
            temp_file_path = temp_f.name

        pattern = read(temp_file_path)

        if pattern is None:
            return jsonify({"error": "Could not parse embroidery pattern. File may be corrupt or unsupported."}), 400

        image = pattern.get_image()
        if image is None:
            return jsonify({"error": "Failed to generate image from pattern"}), 500

        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        # --- START OF THE FIX ---
        # This will print the full, detailed error to the Railway logs
        traceback.print_exc()  # <--- 2. ADD THIS LINE
        # --- END OF THE FIX ---
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)