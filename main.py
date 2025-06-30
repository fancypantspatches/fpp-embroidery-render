import os
from pyembroidery import read
from PIL import Image

# --- Configuration ---
# Specify the embroidery file you want to process.
# In a real application, you might get this from a user upload, an API request, or a database.
EMBROIDERY_FILE_PATH = "example.dst"  # IMPORTANT: Replace "example.dst" with the path to your file.

# Specify the desired output path for the rendered image.
OUTPUT_IMAGE_PATH = "output.png"

def render_embroidery_file(input_path, output_path):
    """
    Reads an embroidery file and saves it as a PNG image.

    Args:
        input_path (str): The path to the input embroidery file (e.g., .dst, .pes).
        output_path (str): The path to save the output PNG image.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Check if the input file exists before attempting to read it.
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'")
        return False

    print(f"Reading embroidery pattern from '{input_path}'...")
    try:
        # The 'read' function parses the file into an EmbroideryPattern object.
        pattern = read(input_path)
    except Exception as e:
        # Catching potential errors during file parsing.
        print(f"Error reading or parsing the file: {e}")
        return False

    # If the pattern is None, it means the file was empty or couldn't be parsed.
    if pattern is None:
        print("Error: Failed to read embroidery pattern. The file might be corrupt or unsupported.")
        return False

    print("Pattern read successfully. Generating image...")
    
    # Use the .get_image() method on the pattern object to render the image.
    # This method returns a standard Python Imaging Library (PIL) Image object.
    image = pattern.get_image()

    if image:
        try:
            # Save the PIL image to the specified output path.
            image.save(output_path)
            print(f"Success! Image saved to '{output_path}'")
            return True
        except Exception as e:
            print(f"Error saving the image: {e}")
            return False
    else:
        print("Error: Could not generate an image from the pattern.")
        return False

if __name__ == "__main__":
    # This block runs when the script is executed directly.
    # In your Railway deployment, you might call the render_embroidery_file function
    # from within a web framework like Flask or FastAPI.
    
    # Before running, create a placeholder file or use a real one.
    # For this example to run, you MUST have a file named "example.dst"
    # in the same directory as this script.
    
    # You can create a dummy file for testing if you don't have one:
    if not os.path.exists(EMBROIDERY_FILE_PATH):
         print(f"Warning: The example file '{EMBROIDERY_FILE_PATH}' was not found.")
         print("Please add an embroidery file to your project to run this script.")
    else:
        render_embroidery_file(EMBROIDERY_FILE_PATH, OUTPUT_IMAGE_PATH)