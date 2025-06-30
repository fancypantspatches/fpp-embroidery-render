import os
import io
import tempfile
import logging
from flask import Flask, request, send_file, jsonify
from pyembroidery import read, STITCH, JUMP, COLOR_CHANGE
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# Initialize the Flask web application
app = Flask(__name__)

@app.route('/')
def health_check():
    """A simple endpoint to confirm that the service is online and running."""
    return jsonify({"status": "ok", "message": "Embroidery Rendering Service is running."})

@app.route('/render-embroidery', methods=['POST'])
def render_embroidery_file():
    """
    Accepts an embroidery file (DST, PES, etc.), renders it with full color,
    and returns a transparent PNG image.
    """
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
            return jsonify({"error": "Could not parse embroidery pattern."}), 400

        bounds = pattern.bounds()
        width = int(bounds[2] - bounds[0])
        height = int(bounds[3] - bounds[1])

        if width <= 0 or height <= 0:
            return jsonify({"error": "Pattern has no valid dimensions."}), 400

        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        thread_index = 0
        current_color_rgb = (0, 0, 0)
        if pattern.threadlist:
             thread = pattern.threadlist[thread_index]
             current_color_rgb = (thread.red, thread.green, thread.blue)

        last_x, last_y = None, None
        for x, y, command in pattern.stitches:
            ix = int(x - bounds[0])
            iy = int(y - bounds[1])
            if command == STITCH and last_x is not None:
                draw.line((last_x, last_y, ix, iy), fill=current_color_rgb, width=2)
            elif command == COLOR_CHANGE:
                thread_index += 1
                if thread_index < len(pattern.threadlist):
                    thread = pattern.threadlist[thread_index]
                    current_color_rgb = (thread.red, thread.green, thread.blue)
            last_x, last_y = ix, iy

        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logging.exception("CRITICAL ERROR IN EMBROIDERY RENDER ENDPOINT:")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)