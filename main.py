from flask import Flask, request, send_file, jsonify
from pyembroidery import read
from PIL import Image, ImageDraw
import requests
import tempfile
import io

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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dst") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        # Read the embroidery pattern
        pattern = read(temp_path)

        # Calculate image size
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

        # Save to in-memory file
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return send_file(img_bytes, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
