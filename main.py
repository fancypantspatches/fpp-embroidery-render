import os
import io
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
    # Check if a file was included in the POST request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Check if a file was actually selected for upload
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file:
        try:
            # Read the embroidery pattern directly from the uploaded file's stream
            pattern = read(file)

            if pattern is None:
                return jsonify({"error": "Could not parse embroidery pattern. File may be corrupt or unsupported."}), 400

            # Generate the image using the correct .get_image() method
            image = pattern.get_image()

            if image is None:
                return jsonify({"error": "Failed to generate image from pattern"}), 500

            # Save the image to an in-memory buffer instead of a file on disk
            img_io = io.BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0) # Rewind the buffer to the beginning

            # Send the image buffer as the HTTP response
            return send_file(img_io, mimetype='image/png')

        except Exception as e:
            # Return a generic server error if anything goes wrong
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    return jsonify({"error": "Invalid file"}), 400

if __name__ == '__main__':
    # Get the port from the environment variable Railway provides
    port = int(os.environ.get("PORT", 8080))
    # Run the app, listening on all network interfaces
    app.run(host='0.0.0.0', port=port)