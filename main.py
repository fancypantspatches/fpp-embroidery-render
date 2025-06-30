import os
import io
import tempfile
from flask import Flask, request, send_file, jsonify
from pyembroidery import read

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def health_check():
    """
    A simple health-check endpoint to confirm the server is running.
    """
    return jsonify({"status": "ok", "message": "Embroidery rendering service is running."})

@app.route('/render', methods=['POST'])
def render_embroidery_file():
    """
    This endpoint accepts a file upload, renders it as a PNG,
    and returns the image directly in the response.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # --- START OF THE FIX ---
    # We will save the uploaded file to a temporary file first
    temp_file_path = None
    try:
        # Create a temporary file and get its path
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.filename) as temp_f:
            uploaded_file.save(temp_f)
            temp_file_path = temp_f.name

        # Now, use the temporary file's PATH with pyembroidery.read()
        pattern = read(temp_file_path)
        # --- END OF THE FIX ---

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
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        # This block ensures the temporary file is deleted even if an error occurs
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)