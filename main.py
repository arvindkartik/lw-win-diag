import cv2
import numpy as np
import mss
import pyautogui
import time
import os
import keyboard
import sys
import random
import ctypes
import requests

def send_ntfy_alert(message):
    try:
        requests.post("https://ntfy.sh/r_wind_diag",
            data=message.encode(encoding='utf-8'),
            headers={
                "Title": "Windows Diagnostics Alert",
                "Priority": "urgent",
                "Tags": "warning"
            })
    except Exception as e:
        print(f"      [!] Failed to send mobile alert: {e}")

# --- CONFIGURATION ---

def safe_reset_click():
    """Click a safe off‑screen area (1000 px from top, 300 px from right)."""
    width, _ = pyautogui.size()
    pyautogui.click(width - 300, 1000)
MONITOR_NUMBER = 1
TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

SQUAD_BUSY_WAIT = 2  # seconds
SQUAD_LIMIT = 4

def check_kill_switch():
    """Instantly kills the script if 'q' is pressed."""
    if keyboard.is_pressed('q'):
        print("\n[!] Kill switch 'q' pressed. Exiting safely...")
        sys.exit(0)

def get_screenshot(crop_right_half=False):
    with mss.mss() as sct:
        if MONITOR_NUMBER >= len(sct.monitors):
            monitor = sct.monitors[0]
        else:
            monitor = sct.monitors[MONITOR_NUMBER]

        if crop_right_half:
            monitor = {
                "top": monitor["top"],
                "left": monitor["left"] + (monitor["width"] // 2),
                "width": monitor["width"] // 2,
                "height": monitor["height"]
            }
        screenshot = sct.grab(monitor)
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        return frame, monitor

def count_active_squads():
    """Count how many squads are currently busy marching/returning."""
    path = os.path.join(TEMPLATE_DIR, 'go_status.jpg')
    if not os.path.exists(path):
        return 0
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    frame, _ = get_screenshot(crop_right_half=False)
    res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.85
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))
    if not points:
        return 0
    clusters = []
    for pt in points:
        is_new = True
        for cluster in clusters:
            if abs(pt[0] - cluster[0]) < 20 and abs(pt[1] - cluster[1]) < 20:
                is_new = False
                break
        if is_new:
            clusters.append(pt)
    return len(clusters)

def find_and_click_ui(template_path, threshold=0.7, timeout=3, crop_right_half=True):
    """Scan for a UI element and click its center if found."""
    if not os.path.exists(template_path):
        print(f"      [!] Template missing: {os.path.basename(template_path)}")
        return False
        
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return False
        
    h, w = template.shape[:2]
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        check_kill_switch()
        frame, monitor = get_screenshot(crop_right_half=crop_right_half)
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            # Add a random offset between -10 and +10 pixels to avoid anti-cheat detection
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            abs_x = monitor["left"] + max_loc[0] + w // 2 + offset_x
            abs_y = monitor["top"] + max_loc[1] + h // 2 + offset_y
            
            # Randomize movement duration slightly
            move_duration = random.uniform(0.15, 0.35)
            pyautogui.moveTo(abs_x, abs_y, duration=move_duration)
            pyautogui.click()
            return True
            
        time.sleep(0.1)
    return False

def is_ui_present(template_path, threshold=0.7, timeout=0.5, crop_right_half=False):
    """Scan for a UI element and return True if found, without clicking."""
    if not os.path.exists(template_path):
        print(f"      [!] Template missing: {os.path.basename(template_path)}")
        return False
        
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return False
        
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        check_kill_switch()
        frame, monitor = get_screenshot(crop_right_half=crop_right_half)
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            return True
            
        time.sleep(0.1)
    return False

def main_loop():
    # Change the console window title to something generic to avoid detection
    ctypes.windll.kernel32.SetConsoleTitleW("Windows System Diagnostics")
    
    print("\n" + "=" * 50)
    print("Diagnostics Handler Running...")
    print(f"[*] Max threads allocated: {SQUAD_LIMIT}")
    print("Press and hold 'q' at any time to abort.")
    print("=" * 50 + "\n")
    time.sleep(0.3)
    
    send_ntfy_alert("Diagnostics Handler has started! 🚀")

    events_path = os.path.join(TEMPLATE_DIR, 'events_button.jpg')
    search_path = os.path.join(TEMPLATE_DIR, 'search.jpg')
    attack_path = os.path.join(TEMPLATE_DIR, 'attack_button.jpg')
    march_path = os.path.join(TEMPLATE_DIR, 'march_button.jpg')
    quit_game_path = os.path.join(TEMPLATE_DIR, 'quit_game_menu.jpg')

    consecutive_failures = 0
    total_marches = 0
    was_stuck = False

    while True:
        check_kill_switch()
        squads_busy = count_active_squads()
        
        # 1. Wait for available squad
        if squads_busy >= SQUAD_LIMIT:
            print(f"[{time.strftime('%H:%M:%S')}] {squads_busy}/{SQUAD_LIMIT} squads busy. Waiting {SQUAD_BUSY_WAIT}s...")
            time.sleep(SQUAD_BUSY_WAIT)
            continue

        print(f"[{time.strftime('%H:%M:%S')}] {SQUAD_LIMIT - squads_busy}/{SQUAD_LIMIT} squads available! Starting search sequence...")

        # 2. Click Events Button
        print(">>> Opening Events menu...")
        if not find_and_click_ui(events_path, threshold=0.7, timeout=1.0, crop_right_half=True):
            print("      [!] Could not find Events button. Pressing Esc...")
            pyautogui.press('esc')
            time.sleep(0.5)
            
            if is_ui_present(quit_game_path, threshold=0.7, timeout=1.0, crop_right_half=False):
                print("      [!] Quit game menu detected. Pressing Esc again to dismiss...")
                pyautogui.press('esc')
                time.sleep(0.5)
                
            consecutive_failures += 1
            if consecutive_failures >= 4:
                print("      [!] Stuck in events loop. Sending alert...")
                send_ntfy_alert("Bot is stuck looking for Events button.")
                was_stuck = True
                consecutive_failures = 0
            continue
        time.sleep(0.5) # Wait for menu to open

        # 3. Click Search Button
        print(">>> Clicking Search...")
        if not find_and_click_ui(search_path, threshold=0.7, timeout=2.0, crop_right_half=True):
            print("      [!] Could not find Search button. Clicking off to reset...")
            safe_reset_click()
            consecutive_failures += 1
            if consecutive_failures >= 4:
                print("      [!] Stuck in search loop. Sending alert...")
                send_ntfy_alert("Bot is stuck looking for Search button.")
                was_stuck = True
                consecutive_failures = 0
            continue
        time.sleep(1.0) # Game needs time to auto-select zombie and bring up attack menu

        # 4. Click Attack
        print(">>> Clicking Attack!")
        if not find_and_click_ui(attack_path, threshold=0.7, timeout=3.0, crop_right_half=True):
            print("      [!] Could not find Attack button. Resetting...")
            safe_reset_click()
            consecutive_failures += 1
            if consecutive_failures >= 4:
                print("      [!] Stuck in attack loop. Sending alert...")
                send_ntfy_alert("Bot is stuck looking for Attack button.")
                was_stuck = True
                consecutive_failures = 0
            continue
        time.sleep(0.5)

        # 5. Click March
        print(">>> Clicking March!")
        if find_and_click_ui(march_path, threshold=0.7, timeout=3.0, crop_right_half=True):
            print(">>> Squad Marched! Success.")
            if was_stuck:
                send_ntfy_alert("Bot has successfully recovered and resumed marching! 🟢")
                was_stuck = False
            consecutive_failures = 0  # Reset on complete success
            total_marches += 1
            if total_marches % 100 == 0:
                send_ntfy_alert(f"Milestone Reached: {total_marches} successful marches! 🎉")
            elif total_marches % 20 == 0:
                send_ntfy_alert(f"Progress Update: {total_marches} successful marches! ✅")
            time.sleep(1.0) # Let the march animation start before repeating
        else:
            print("      [!] Could not find March button. Resetting...")
            safe_reset_click()
            consecutive_failures += 1
            if consecutive_failures >= 4:
                print("      [!] Stuck in march loop. Sending alert...")
                send_ntfy_alert("Bot is stuck looking for March button.")
                was_stuck = True
                consecutive_failures = 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            SQUAD_LIMIT = int(sys.argv[1])
        except ValueError:
            print(f"[!] Invalid squad limit '{sys.argv[1]}'. Using default: {SQUAD_LIMIT}")
            
    pyautogui.FAILSAFE = True
    main_loop()
