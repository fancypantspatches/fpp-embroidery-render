import os
import io
import tempfile
import logging
from flask import Flask, request, send_file, jsonify
from pyembroidery import read
from PIL import Image, ImageDraw # <-- Make sure ImageDraw is imported

# Configure the logging system
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

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
            return jsonify({"error": "Could not parse embroidery pattern."}), 400

        # --- START OF THE FINAL FIX ---
        # Manually render the image by drawing each stitch. This is the correct way.
        bounds = pattern.bounds()
        width = int(bounds[2] - bounds[0])
        height = int(bounds[3] - bounds[1])

        if width <= 0 or height <= 0:
            return jsonify({"error": "Pattern has no dimensions."}), 400

        image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(image)

        for stitch in pattern.stitches:
            x1 = int(stitch[0] - bounds[0])
            y1 = int(stitch[1] - bounds[1])
            x2 = int(stitch[2] - bounds[0])
            y2 = int(stitch[3] - bounds[1])
            color = pattern.threadlist[stitch[4]].color
            draw.line((x1, y1, x2, y2), fill=(color.red, color.green, color.blue), width=3)
        # --- END OF THE FINAL FIX ---

        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logging.exception("CRITICAL ERROR IN RENDER ENDPOINT:")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)