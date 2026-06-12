import cv2
import os

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

img_path = os.path.join(TEMPLATE_DIR, 'squad_selection.jpg')
img = cv2.imread(img_path, cv2.IMREAD_COLOR)

if img is not None:
    line_templates = ['arrow_line_green.jpg', 'arrow_line_white.jpg']
    for t_name in line_templates:
        t_path = os.path.join(TEMPLATE_DIR, t_name)
        template = cv2.imread(t_path, cv2.IMREAD_COLOR)
        if template is not None:
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            print(f"Max score for {t_name} on squad_selection.jpg: {max_val:.4f}")
