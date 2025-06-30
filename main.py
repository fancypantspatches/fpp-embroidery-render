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
        # Securely save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.filename)[1]) as temp_f:
            uploaded_file.save(temp_f)
            temp_file_path = temp_f.name

        logging.info(f"Reading file: {temp_file_path}")
        pattern = read(temp_file_path)

        if pattern is None:
            logging.error("Failed to parse embroidery pattern.")
            return jsonify({"error": "Could not parse embroidery pattern."}), 400

        # Get the design's bounding box to calculate image size
        bounds = pattern.bounds()
        width = int(bounds[2] - bounds[0])
        height = int(bounds[3] - bounds[1])

        if width <= 0 or height <= 0:
            logging.warning("Pattern has no valid dimensions.")
            return jsonify({"error": "Pattern has no valid dimensions."}), 400
        
        logging.info(f"Creating image with dimensions: {width}x{height}")
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0)) # Transparent background
        draw = ImageDraw.Draw(image)

        # --- CORRECTED COLOR AND DRAWING LOGIC ---

        # Use the thread.get_rgb() method which works for all thread types
        colors = [thread.get_rgb() for thread in pattern.threadlist]
        
        if not colors:
            # Fallback for files like DST that have no color info
            colors = [(0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0)] 

        thread_index = 0
        # Start with the very first color
        current_color_rgb = colors[0]

        last_x, last_y = None, None

        for x, y, command in pattern.stitches:
            # Translate stitch coordinates to image coordinates
            ix = int(x - bounds[0])
            iy = int(y - bounds[1])

            if command == COLOR_CHANGE:
                thread_index += 1
                # Cycle through colors if there are more changes than defined colors
                current_color_rgb = colors[thread_index % len(colors)]
                # A color change command doesn't have a stitch, so we skip to the next command
                continue

            # If the command is a JUMP, break the line. Don't draw it.
            if command == JUMP:
                last_x, last_y = None, None
                continue

            # If the command is a STITCH and we have a previous point, draw the line
            if command == STITCH and last_x is not None:
                draw.line((last_x, last_y, ix, iy), fill=current_color_rgb, width=2)
            
            # Update the last position
            last_x, last_y = ix, iy

        # --- END OF CORRECTED LOGIC ---

        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        logging.info("Successfully rendered and sending image.")
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logging.exception("CRITICAL ERROR IN EMBROIDERY RENDER ENDPOINT:")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)