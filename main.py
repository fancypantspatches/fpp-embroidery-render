from flask import Flask, request, send_file, jsonify
from pyembroidery import read

from PIL import Image, ImageDraw
import requests
import tempfile
import os

app = Flask(__name__)

@app.route("/render", methods=["POST"])
def render():
    data = request.get_json()
    file_url = data.get("fileUrl")

    if not file_url:
        return jsonify({"error": "Missing fileUrl"}), 400

    try:
        # Download embroidery file
        response = requests.get(file_url)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".emb") as temp_emb:
            temp_emb.write(response.content)
            temp_emb_path = temp_emb.name

        # Read embroidery file
        pattern = read(temp_emb_path)

        xmin, ymin, xmax, ymax = pattern.extents()
        width = int(xmax - xmin + 20)
        height = int(ymax - ymin + 20)

        # Render image
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        current_pos = None
        for stitch in pattern.stitches:
            x, y = stitch[0] - xmin + 10, stitch[1] - ymin + 10
            if current_pos:
                draw.line([current_pos, (x, y)], fill="black", width=1)
            current_pos = (x, y)

        # Save to temporary file
        preview_path = temp_emb_path.replace(".emb", "_preview.png")
        img.save(preview_path)

        return send_file(preview_path, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

