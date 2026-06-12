import cv2
import os
import numpy as np

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

def test_strict(img_name):
    img_path = os.path.join(TEMPLATE_DIR, img_name)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if img is not None:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Extremely strict range
        lower_neon = np.array([34, 120, 145])
        upper_neon = np.array([38, 160, 180])
        
        mask = cv2.inRange(hsv, lower_neon, upper_neon)
        count = cv2.countNonZero(mask)
        print(f"Pixels in {img_name}: {count}")
    else:
        print(f"Could not load {img_name}")

test_strict('free_zombie.jpg')
test_strict('arrow_single_green.jpg')
