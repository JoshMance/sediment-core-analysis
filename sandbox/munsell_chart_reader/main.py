import os
from PIL import Image


# Directory containing the images (test_images subfolder relative to this script)
image_dir = os.path.join(os.path.dirname(__file__), 'test_images')
all_files = os.listdir(image_dir) if os.path.exists(image_dir) else []

image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

images = []
for filename in image_files:
    path = os.path.join(image_dir, filename)
    try:
        img = Image.open(path)
        images.append((filename, img))
        print(f"Loaded: {filename} - size: {img.size}, mode: {img.mode}")
    except Exception as e:
        print(f"Failed to load {filename}: {e}")

# images is now a list of (filename, Image) tuples