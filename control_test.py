import cv2
import numpy as np
import mss
import pyautogui
import time
import os

def find_and_click(template_path, threshold=0.7, timeout=5):
    """
    Takes screenshots continuously until the template is found or timeout is reached.
    If found, clicks the center of the match.
    """
    sct = mss.mss()
    monitor_number = 1
    monitor = sct.monitors[monitor_number]
    
    # We crop to the right half of the screen just like the vision test
    monitor = {
        "top": monitor["top"],
        "left": monitor["left"] + (monitor["width"] // 2),
        "width": monitor["width"] // 2,
        "height": monitor["height"]
    }
    
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"Error: Could not load {template_path}")
        return False
        
    h, w = template.shape[:2]
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        screenshot = sct.grab(monitor)
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            # Found it! Calculate center relative to the cropped monitor
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            # Convert to absolute screen coordinates
            abs_x = monitor["left"] + center_x
            abs_y = monitor["top"] + center_y
            
            print(f"Found {os.path.basename(template_path)} at ({abs_x}, {abs_y}) with confidence {max_val:.2f}")
            
            # Move mouse smoothly and click
            pyautogui.moveTo(abs_x, abs_y, duration=0.3)
            pyautogui.click()
            return True
            
        # Give the game a moment to render the next frame
        time.sleep(0.2)
        
    print(f"Timeout: Could not find {os.path.basename(template_path)}")
    return False

def control_test():
    print("--- STARTING PHASE 2 CONTROL TEST ---")
    print("Please make sure the game is visible and you have a zombie on screen.")
    print("You have 3 seconds to switch to the game window...")
    time.sleep(3)

    # 1. Find a zombie
    print("\n[Step 1] Looking for a zombie...")
    template_dir = os.path.join('source_images', '2026-05-28')
    zombie_images = ['1.jpg', '2.jpg', '3.jpg']
    
    zombie_found = False
    for z in zombie_images:
        path = os.path.join(template_dir, z)
        if os.path.exists(path):
            # Try to find the zombie. Lowered threshold slightly just to be safe.
            if find_and_click(path, threshold=0.6, timeout=3): 
                zombie_found = True
                print(">>> Clicked Zombie!")
                break
                
    if not zombie_found:
        print(">>> Failed: Could not find any zombies on screen.")
        return

    # 2. Wait for attack button and click it
    print("\n[Step 2] Waiting for Attack button to appear...")
    time.sleep(0.5) # Small pause to let game UI animate
    attack_path = os.path.join(template_dir, 'attack_button.jpg')
    if find_and_click(attack_path, threshold=0.7, timeout=5):
        print(">>> Clicked Attack!")
    else:
        print(">>> Failed: Could not find Attack button.")
        return
        
    # 3. Wait for march button and click it
    print("\n[Step 3] Waiting for March button to appear...")
    time.sleep(0.5)
    squad_path = os.path.join(template_dir, 'march_button.jpg')
    if find_and_click(squad_path, threshold=0.7, timeout=5):
        print(">>> Clicked March! Sequence complete.")
    else:
        print(">>> Failed: Could not find March button.")

if __name__ == '__main__':
    control_test()
