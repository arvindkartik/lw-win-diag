import cv2
import os
import numpy as np

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

# Load templates
line_templates = ['1.jpg', '2.jpg', '3.jpg']
test_images = ['free_zombie.jpg', 'busy_zombie.jpg', 'busy_zombie1.jpg']

for test_img_name in test_images:
    test_path = os.path.join(TEMPLATE_DIR, test_img_name)
    img = cv2.imread(test_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Could not load {test_path}")
        continue
    
    print(f"\n--- Testing on {test_img_name} ---")
    
    for template_name in line_templates:
        temp_path = os.path.join(TEMPLATE_DIR, template_name)
        template = cv2.imread(temp_path, cv2.IMREAD_COLOR)
        if template is None:
            continue
        
        # Test match
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        print(f"Template {template_name}: max score = {max_val:.4f}")
