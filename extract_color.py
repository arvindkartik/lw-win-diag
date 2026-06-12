import cv2
import os
import numpy as np
from collections import Counter

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')
img_path = os.path.join(TEMPLATE_DIR, 'arrow_single_green.jpg')

img = cv2.imread(img_path, cv2.IMREAD_COLOR)
if img is not None:
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Flatten array to list of pixels
    pixels = hsv.reshape(-1, 3)
    
    # Filter out black/dark background pixels (Value < 50) or very low saturation
    valid_pixels = [p for p in pixels if p[2] > 50 and p[1] > 50]
    
    if len(valid_pixels) > 0:
        hues = [p[0] for p in valid_pixels]
        sats = [p[1] for p in valid_pixels]
        vals = [p[2] for p in valid_pixels]
        
        # Calculate median to find the most representative color
        med_h = np.median(hues)
        med_s = np.median(sats)
        med_v = np.median(vals)
        
        # Also print min/max for bounds
        print(f"Median HSV: H={med_h}, S={med_s}, V={med_v}")
        print(f"Min HSV: H={np.min(hues)}, S={np.min(sats)}, V={np.min(vals)}")
        print(f"Max HSV: H={np.max(hues)}, S={np.max(sats)}, V={np.max(vals)}")
    else:
        print("No valid non-dark pixels found.")
else:
    print("Could not load image.")
