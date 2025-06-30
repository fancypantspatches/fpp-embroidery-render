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
        # Download the embroidery file
        response = requests.get(file_url)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".emb") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        # Read the embroidery pattern
        pattern = read(temp_path)

        # Get extents for sizing the image
        extents = pattern.extents()
        xmin, ymin, xmax, ymax = extents
        width = int(xmax - xmin + 20)
        height = int(ymax - ymin + 20)

        # Create a blank image and draw the stitches
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        current_pos = None
        for stitch in pattern.stitches:
            x, y = stitch[0] - xmin + 10, stitch[1] - ymin + 10
            if current_pos:
                draw.line([current_pos, (x, y)], fill="black", width=1)
            current_pos = (x, y)

        # Save to temporary image file
        preview_path = temp_path.replace(".emb", "_preview.png")
        img.save(preview_path)

        return send_file(preview_path, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
