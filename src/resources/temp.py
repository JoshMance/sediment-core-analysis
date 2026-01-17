# raccoon_face_demo.py
import matplotlib.pyplot as plt
import numpy as np
from scipy.datasets import face
from imageio.v3 import imwrite

# -----------------------
# Load the classic raccoon face
# -----------------------
img_color = face()  # shape: (768, 1024, 3), RGB

# -----------------------
# Display color image
# -----------------------
plt.figure(figsize=(8,6))
plt.imshow(img_color)
plt.axis('off')
plt.title("Raccoon Face (Color)")
plt.show()

# -----------------------
# Convert to grayscale
# -----------------------
# Simple RGB to grayscale conversion
img_gray = np.dot(img_color[...,:3], [0.2989, 0.5870, 0.1140])

plt.figure(figsize=(8,6))
plt.imshow(img_gray, cmap='gray')
plt.axis('off')
plt.title("Raccoon Face (Grayscale)")
plt.show()

# -----------------------
# Save both images to disk
# -----------------------
imwrite("raccoon_face_color.png", img_color)
imwrite("raccoon_face_gray.png", img_gray.astype(np.uint8))

print("Images saved as 'raccoon_face_color.png' and 'raccoon_face_gray.png'")
