import cv2
import os
import numpy as np

TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

test_images = ['free_zombie.jpg', 'busy_zombie.jpg', 'busy_zombie1.jpg']

def analyze_colors(img_name):
    path = os.path.join(TEMPLATE_DIR, img_name)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return
    
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define ranges for green and white
    # Green arrow line
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    
    # White arrow line (usually high value, low saturation)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    
    green_pixels = cv2.countNonZero(mask_green)
    white_pixels = cv2.countNonZero(mask_white)
    
    print(f"--- {img_name} ---")
    print(f"Green pixels: {green_pixels} ({(green_pixels / (img.shape[0]*img.shape[1]))*100:.2f}%)")
    print(f"White pixels: {white_pixels} ({(white_pixels / (img.shape[0]*img.shape[1]))*100:.2f}%)")

for name in test_images:
    analyze_colors(name)
