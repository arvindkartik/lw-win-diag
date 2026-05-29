import cv2
import numpy as np
import mss
import pyautogui
import time
import os
import keyboard
import sys
import math

# --- CONFIGURATION ---
MONITOR_NUMBER = 1

# Recent zombie memory to avoid re‑attacking the same target too quickly
TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')

SQUAD_BUSY_WAIT = 2  # seconds
ZOMBIE_BLOCK_DURATION = 30  # seconds (unused, kept for potential future tweaks)
SQUAD_LIMIT = 4  # maximum number of squads


def check_kill_switch():
    """Instantly kills the script if 'q' is pressed."""
    if keyboard.is_pressed('q'):
        print("\n[!] Kill switch 'q' pressed. Exiting safely...")
        sys.exit(0)

def _cleanup_recent():
    """Remove expired entries from the recent zombie cache."""
    now = time.time()
    expired = [k for k, v in _recent_zombies.items() if now - v > RECENT_ZOMBIE_TTL]
    for k in expired:
        del _recent_zombies[k]

def _mark_recent(coord):
    """Record a zombie coordinate as recently attacked."""
    _recent_zombies[coord] = time.time()

def _is_recent(coord):
    """Check if a coordinate was recently attacked."""
    _cleanup_recent()
    return coord in _recent_zombies
    if keyboard.is_pressed('q'):
        print("\n[!] Kill switch 'q' pressed. Exiting safely...")
        sys.exit(0)

def get_screenshot(crop_right_half=False):
    sct = mss.mss()
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

def is_zombie_busy(abs_x, abs_y, frame, monitor):
    """Detect arrow lines (green or white) near the zombie."""
    # Convert to frame‑relative
    frame_x = abs_x - monitor["left"]
    frame_y = abs_y - monitor["top"]
    search_radius = 350  # pixels, larger to catch lines extending outwards
    x1 = max(0, frame_x - search_radius)
    y1 = max(0, frame_y - search_radius)
    x2 = min(frame.shape[1], frame_x + search_radius)
    y2 = min(frame.shape[0], frame_y + search_radius)
    roi = frame[y1:y2, x1:x2]

    line_templates = ['arrow_line_green.jpg', 'arrow_line_white.jpg']
    for line_img in line_templates:
        line_path = os.path.join(TEMPLATE_DIR, line_img)
        if not os.path.exists(line_path):
            continue
        line_template = cv2.imread(line_path, cv2.IMREAD_COLOR)
        if line_template is None:
            continue
        res = cv2.matchTemplate(roi, line_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= 0.45:
            line_center_x = x1 + max_loc[0] + line_template.shape[1] // 2
            line_center_y = y1 + max_loc[1] + line_template.shape[0] // 2
            distance = math.hypot(line_center_x - abs_x, line_center_y - abs_y)
            if distance <= 150:
                return True, f"Line {line_img} detected (score={max_val:.2f})"
    return False, ""

def find_free_zombie_and_click(template_paths, threshold=0.6, timeout=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        check_kill_switch()
        frame, monitor = get_screenshot(crop_right_half=True)
        for path in template_paths:
            if not os.path.exists(path):
                continue
            template = cv2.imread(path, cv2.IMREAD_COLOR)
            if template is None:
                continue
            h, w = template.shape[:2]
            res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            points = list(zip(*loc[::-1]))
            for pt in points:
                abs_x = monitor["left"] + pt[0] + w // 2
                abs_y = monitor["top"] + pt[1] + h // 2
                # Skip if this zombie was recently targeted
                if _is_recent((abs_x, abs_y)):
                    continue
                busy, _ = is_zombie_busy(abs_x, abs_y, frame, monitor)
                if busy:
                    continue
                pyautogui.moveTo(abs_x, abs_y, duration=0.2)
                pyautogui.click()
                # Mark as recent to avoid immediate re‑selection by another squad
                _mark_recent((abs_x, abs_y))
                return True, (abs_x, abs_y)
        time.sleep(0.1)
    return False, None

def find_and_click_ui(template_path, threshold=0.7, timeout=3):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return False
    h, w = template.shape[:2]
    start_time = time.time()
    while time.time() - start_time < timeout:
        check_kill_switch()
        frame, monitor = get_screenshot(crop_right_half=True)
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            abs_x = monitor["left"] + max_loc[0] + w // 2
            abs_y = monitor["top"] + max_loc[1] + h // 2
            pyautogui.moveTo(abs_x, abs_y, duration=0.2)
            pyautogui.click()
            return True
        time.sleep(0.1)
    return False

def scroll_map():
    print("[Action] Scrolling map down to find new zombies...")
    sct = mss.mss()
    monitor = sct.monitors[MONITOR_NUMBER]
    start_x = monitor["left"] + int(monitor["width"] * 0.75)
    start_y = monitor["top"] + monitor["height"] // 2
    pyautogui.moveTo(start_x, start_y, duration=0.2)
    pyautogui.mouseDown()
    drag_distance = 600
    pyautogui.moveTo(start_x, start_y - drag_distance, duration=0.4)
    pyautogui.mouseUp()
    time.sleep(0.5)

def main_loop():
    print("\n" + "=" * 40)
    print("🧟 LAST WAR ZOMBIE FARMING BOT INITIALIZED 🧟")
    print("Press and hold 'q' at any time to EMERGENCY STOP.")
    print("=" * 40 + "\n")
    time.sleep(0.3)

    zombie_images = [os.path.join(TEMPLATE_DIR, f) for f in ['1.jpg', '2.jpg', '3.jpg']]
    attack_path = os.path.join(TEMPLATE_DIR, 'attack_button.jpg')
    march_path = os.path.join(TEMPLATE_DIR, 'march_button.jpg')
    req_target_path = os.path.join(TEMPLATE_DIR, 'required_target.jpg')

    while True:
        check_kill_switch()
        squads_busy = count_active_squads()
        if squads_busy >= SQUAD_LIMIT:
            print(f"[{time.strftime('%H:%M:%S')}] {squads_busy} squads are busy. Waiting {SQUAD_BUSY_WAIT} seconds...")
            time.sleep(SQUAD_BUSY_WAIT)
            continue

        print(f"[{time.strftime('%H:%M:%S')}] Squads available! Searching for FREE zombie...")
        found, zombie_coords = find_free_zombie_and_click(zombie_images, timeout=0.5)
        if not found:
            scroll_map()
            continue

        print(">>> Free Zombie Clicked! Waiting for UI...")
        time.sleep(0.5)

        # Multi‑target handling
        if os.path.exists(req_target_path):
            if find_and_click_ui(req_target_path, threshold=0.7, timeout=1.5):
                print(">>> Multi‑target list detected! Clicked required target.")
                time.sleep(0.5)

        if find_and_click_ui(attack_path, threshold=0.7, timeout=3):
            print(">>> Clicked Attack!")
            time.sleep(0.3)
            if find_and_click_ui(march_path, threshold=0.7, timeout=3):
                print(">>> Squad Marched! Success.")
                # Small pause to let the arrow line appear before the next iteration
                time.sleep(1.0)
            else:
                print(">>> ERROR: Could not find March button.")
                pyautogui.click(0, 0)
        else:
            print(">>> ERROR: Could not find Attack button.")
            pyautogui.click(0, 0)

if __name__ == '__main__':
    pyautogui.FAILSAFE = True
    main_loop()
