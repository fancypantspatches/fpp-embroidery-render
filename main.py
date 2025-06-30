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
        logging.warning("No file part in the request.")
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        logging.warning("No file selected.")
        return jsonify({"error": "No file selected"}), 400

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.filename)[1]) as temp_f:
            uploaded_file.save(temp_f)
            temp_file_path = temp_f.name

        logging.info(f"Reading file: {temp_file_path}")
        pattern = read(temp_file_path)

        if pattern is None:
            logging.error("Failed to parse embroidery pattern.")
            return jsonify({"error": "Could not parse embroidery pattern."}), 400

        bounds = pattern.bounds()
        
        if None in bounds:
            logging.error("Pattern bounds could not be determined. File may be empty or corrupt.")
            return jsonify({"error": "Pattern has invalid dimensions; file may be empty or corrupt."}), 400

        width = int(bounds[2] - bounds[0])
        height = int(bounds[3] - bounds[1])

        if width <= 0 or height <= 0:
            logging.warning("Pattern has zero or negative dimensions.")
            return jsonify({"error": "Pattern has no valid dimensions."}), 400
        
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        colors = [thread.color for thread in pattern.threadlist if thread.color is not None]
        
        if not colors:
            colors = [(0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0)] 

        if not colors:
            logging.error("Pattern contains no valid colors to render.")
            return jsonify({"error": "Pattern contains no valid colors to render."}), 400

        thread_index = 0
        current_color_rgb = colors[0]
        last_x, last_y = None, None

        for x, y, command in pattern.stitches:
            if x is None or y is None:
                continue 

            ix = int(x - bounds[0])
            iy = int(y - bounds[1])

            if command == COLOR_CHANGE:
                thread_index += 1
                current_color_rgb = colors[thread_index % len(colors)]
                continue

            if command == JUMP:
                last_x, last_y = None, None
                continue

            if command == STITCH and last_x is not None:
                draw.line((last_x, last_y, ix, iy), fill=current_color_rgb, width=2)
            
            last_x, last_y = ix, iy

        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        logging.info("Successfully rendered. Sending PNG image.")
        
        # --- NEW DYNAMIC FILENAME LOGIC ---
        base_filename = os.path.splitext(uploaded_file.filename)[0]
        png_filename = f"{base_filename}.png"
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=png_filename
        )

    except Exception as e:
        logging.exception("CRITICAL ERROR IN EMBROIDERY RENDER ENDPOINT:")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)