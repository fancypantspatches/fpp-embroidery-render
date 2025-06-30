from flask import Flask, request, send_file
from pyembroidery import read, render_image
import requests
import re

app = Flask(__name__)

def to_snake_case(name):
    return re.sub(r'[^a-zA-Z0-9]', '_', name).lower()

@app.route("/render", methods=["POST"])
def render():
    file_url = request.json.get("fileUrl")
    if not file_url:
        return {"error": "Missing fileUrl"}, 400

    ext = ".pes" if ".pes" in file_url.lower() else ".dst"
    file_name = f"design{ext}"
    output_name = f"{to_snake_case(file_name.split('.')[0])}_preview.png"

    r = requests.get(file_url)
    with open(file_name, "wb") as f:
        f.write(r.content)

    pattern = read(file_name)
    render_image(pattern, output_name)

    return send_file(output_name, mimetype="image/png")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

