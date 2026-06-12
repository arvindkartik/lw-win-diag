import cv2
import os

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

img_path = os.path.join(TEMPLATE_DIR, 'free_zombie.jpg')
t_path = os.path.join(TEMPLATE_DIR, 'single_array.jpg')

img = cv2.imread(img_path, cv2.IMREAD_COLOR)
template = cv2.imread(t_path, cv2.IMREAD_COLOR)

if img is not None and template is not None:
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    print(f"Max score: {max_val:.4f} at {max_loc}")
    h, w = template.shape[:2]
    # Crop the match from free_zombie.jpg
    match_crop = img[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
    # Save the crop
    cv2.imwrite('match_crop.jpg', match_crop)
    
