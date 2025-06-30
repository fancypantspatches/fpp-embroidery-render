import requests
from pyembroidery import read_dst
from PIL import Image, ImageDraw
import io

# ✅ 1. Use your actual Google Drive file
file_url = "https://drive.google.com/uc?export=download&id=1v78AWNcql8MGHz8769-sKk6MwKL7dsG-"

print("⬇️ Downloading file...")
response = requests.get(file_url)
with open("test.dst", "wb") as f:
    f.write(response.content)
print("📦 Saved as test.dst")

# ✅ 2. Read and render
pattern = read_dst("test.dst")

# Use the real bounding box (xmin, ymin, xmax, ymax)
xmin, ymin, xmax, ymax = pattern.extents()
width = int(xmax - xmin + 20)
height = int(ymax - ymin + 20)

# ✅ 3. Create blank canvas with padding
image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)

# ✅ 4. Draw the stitches
current_pos = None
for stitch in pattern.stitches:
    x, y = stitch[0] - xmin + 10, stitch[1] - ymin + 10  # offset to fit in image
    if current_pos:
        draw.line([current_pos, (x, y)], fill="black", width=1)
    current_pos = (x, y)

# ✅ 5. Save preview image
preview_path = "test_preview.png"
image.save(preview_path)
print(f"✅ Preview created: {preview_path}")
