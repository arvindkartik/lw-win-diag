import cv2
import os
import numpy as np

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')
line_templates = ['arrow_line_green.jpg', 'arrow_line_white.jpg', 'single_array.jpg']
test_images = ['busy_zombie.jpg', 'busy_zombie1.jpg']

for test_img_name in test_images:
    test_path = os.path.join(TEMPLATE_DIR, test_img_name)
    img = cv2.imread(test_path, cv2.IMREAD_COLOR)
    if img is None:
        continue
    
    print(f"\n--- Testing on {test_img_name} ---")
    
    for t_name in line_templates:
        t_path = os.path.join(TEMPLATE_DIR, t_name)
        template = cv2.imread(t_path, cv2.IMREAD_COLOR)
        if template is None:
            continue
            
        max_score = 0
        best_angle = 0
        
        # Test rotations
        (h, w) = template.shape[:2]
        center = (w // 2, h // 2)
        
        for angle in range(0, 360, 15):
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(template, rot_mat, (w, h))
            
            # Since the rotated template might have black borders, it might not match well.
            # But let's just try basic matchTemplate
            if img.shape[0] >= rotated.shape[0] and img.shape[1] >= rotated.shape[1]:
                res = cv2.matchTemplate(img, rotated, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > max_score:
                    max_score = max_val
                    best_angle = angle
                    
        print(f"Template {t_name}: max score = {max_score:.4f} at angle {best_angle}")
