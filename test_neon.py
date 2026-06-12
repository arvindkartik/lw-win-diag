import cv2
import os
import numpy as np

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')
img_path = os.path.join(TEMPLATE_DIR, 'free_zombie.jpg')

img = cv2.imread(img_path, cv2.IMREAD_COLOR)
if img is not None:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Yellow-green range from the arrow
    lower_neon = np.array([30, 100, 130])
    upper_neon = np.array([45, 210, 210])
    
    mask = cv2.inRange(hsv, lower_neon, upper_neon)
    count = cv2.countNonZero(mask)
    
    print(f"Neon pixels in free_zombie.jpg: {count}")
    
    # Save the mask to see what it matched (for debugging)
    cv2.imwrite('free_zombie_mask.jpg', mask)
else:
    print("Could not load image.")
