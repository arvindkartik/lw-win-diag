import cv2
import os

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

for name in os.listdir(TEMPLATE_DIR):
    if name.endswith('.jpg'):
        path = os.path.join(TEMPLATE_DIR, name)
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None:
            print(f"{name}: {img.shape}")
