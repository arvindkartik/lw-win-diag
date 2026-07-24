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
import configparser
import paho.mqtt.client as mqtt
import pygetwindow as gw

BOT_STATE = "running"
MQTT_CONFIG = None
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

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

def move_mouse_human(end_x, end_y, duration=0.3):
    """Move the mouse using a randomized bezier curve to simulate human movement."""
    start_x, start_y = pyautogui.position()
    dist = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    
    if dist < 10:
        ctypes.windll.user32.SetCursorPos(int(end_x), int(end_y))
        return

    p0 = np.array([start_x, start_y])
    p3 = np.array([end_x, end_y])
    deviation = min(dist / 4, 150)
    
    p1 = np.array([
        start_x + (end_x - start_x) * random.uniform(0.1, 0.4) + random.uniform(-deviation, deviation),
        start_y + (end_y - start_y) * random.uniform(0.1, 0.4) + random.uniform(-deviation, deviation)
    ])
    p2 = np.array([
        start_x + (end_x - start_x) * random.uniform(0.6, 0.9) + random.uniform(-deviation, deviation),
        start_y + (end_y - start_y) * random.uniform(0.6, 0.9) + random.uniform(-deviation, deviation)
    ])
    
    steps = int(max(dist / 10, 20))
    steps = min(steps, 60)
    sleep_per_step = duration / steps
    
    for i in range(1, steps + 1):
        t = i / steps
        t_eased = t * t * (3.0 - 2.0 * t) # smooth step
        
        pos = (
            (1-t_eased)**3 * p0 +
            3 * (1-t_eased)**2 * t_eased * p1 +
            3 * (1-t_eased) * t_eased**2 * p2 +
            t_eased**3 * p3
        )
        ctypes.windll.user32.SetCursorPos(int(pos[0]), int(pos[1]))
        time.sleep(sleep_per_step)
        
    ctypes.windll.user32.SetCursorPos(int(end_x), int(end_y))

def safe_reset_click():
    """Click a safe off-screen area (1000px from top, 300px from right)."""
    width, _ = pyautogui.size()
    move_mouse_human(width - 300, 1000, duration=0.25)
    pyautogui.click()
MONITOR_NUMBER = 1

LOCAL_TEMPLATE_DIR = os.path.join('local_config', 'templates')
TEMPLATE_DIR = os.path.join('source_images', '2026-05-28')
if os.path.exists(LOCAL_TEMPLATE_DIR) and len(os.listdir(LOCAL_TEMPLATE_DIR)) > 0:
    print("[*] Using custom templates from local_config/templates")
    TEMPLATE_DIR = LOCAL_TEMPLATE_DIR

CONFIG_FILE = os.path.join('local_config', 'config.ini')
WINDOW_BOUNDS = None
if os.path.exists(CONFIG_FILE):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'Window' in config:
        WINDOW_BOUNDS = {
            "left": int(config['Window']['left']),
            "top": int(config['Window']['top']),
            "width": int(config['Window']['width']),
            "height": int(config['Window']['height'])
        }
        print(f"[*] Loaded window bounds from config: {WINDOW_BOUNDS}")
    if 'MQTT' in config:
        MQTT_CONFIG = {
            "broker": config['MQTT'].get('broker', ''),
            "port": int(config['MQTT'].get('port', 8883)),
            "username": config['MQTT'].get('username', ''),
            "password": config['MQTT'].get('password', ''),
            "topic": config['MQTT'].get('topic', 'bot/control'),
            "client_id": config['MQTT'].get('client_id', 'windows-diagnostics-bot')
        }
        print(f"[*] Loaded MQTT config for remote control.")

SQUAD_BUSY_WAIT = 2  # seconds
SQUAD_LIMIT = 4

def check_kill_switch():
    """Instantly kills the script if 'q' is pressed."""
    if keyboard.is_pressed('q'):
        print("\n[!] Kill switch 'q' pressed. Exiting safely...")
        sys.exit(0)

def get_screenshot(crop_right_half=False):
    with mss.mss() as sct:
        if WINDOW_BOUNDS is not None:
            monitor = WINDOW_BOUNDS
        else:
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
    h, w = template.shape[:2]
    frame, _ = get_screenshot(crop_right_half=False)
    res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.80
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))
    if not points:
        return 0
    clusters = []
    for pt in points:
        is_new = True
        for cluster in clusters:
            if abs(pt[0] - cluster[0]) < w and abs(pt[1] - cluster[1]) < h:
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
            move_mouse_human(abs_x, abs_y, duration=move_duration)
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

def setup_mqtt():
    if not MQTT_CONFIG or not MQTT_CONFIG.get("username") or MQTT_CONFIG.get("username") == "YOUR_HIVEMQ_USERNAME":
        print("[*] MQTT not configured or using default placeholders. Remote control disabled.")
        return

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[*] Connected to MQTT broker! Listening for commands...")
            client.subscribe(MQTT_CONFIG["topic"])
        else:
            print(f"[!] Failed to connect to MQTT broker. Code: {rc}")

    def on_message(client, userdata, msg):
        global BOT_STATE
        payload = msg.payload.decode('utf-8').lower().strip()
        if payload == "pause":
            BOT_STATE = "paused"
            send_ntfy_alert("Bot PAUSED via remote control. ⏸️")
            print("\n[*] Received PAUSE command.")
        elif payload == "resume":
            BOT_STATE = "running"
            send_ntfy_alert("Bot RESUMED via remote control. ▶️")
            print("\n[*] Received RESUME command.")
        elif payload == "stop":
            BOT_STATE = "stopped"
            send_ntfy_alert("Bot STOPPED via remote control. ⏹️")
            print("\n[*] Received STOP command.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CONFIG["client_id"])
    client.tls_set() # Enable SSL/TLS
    client.username_pw_set(MQTT_CONFIG["username"], MQTT_CONFIG["password"])
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"], 60)
        client.loop_start()
    except Exception as e:
        print(f"[!] MQTT Connection Error: {e}")

def snap_window_to_right():
    windows = gw.getWindowsWithTitle('Last War-Survival Game')
    if not windows:
        print("      [!] Could not find 'Last War-Survival Game' window to resize.")
        return
        
    win = windows[0]
    
    # Get primary monitor size
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    
    half_width = screen_width // 2
    
    try:
        if win.isMinimized:
            win.restore()
        
        # Unmaximize first if it's maximized
        if win.isMaximized:
            win.restore()
            
        win.moveTo(half_width, 0)
        win.resizeTo(half_width, screen_height)
        
        print(f"[*] Snapped game to right half: Left {half_width}, Width {half_width}x{screen_height}")
        
        # Update our active bounds in memory so mss captures the right area
        global WINDOW_BOUNDS
        if WINDOW_BOUNDS is not None:
            WINDOW_BOUNDS["left"] = half_width
            WINDOW_BOUNDS["top"] = 0
            WINDOW_BOUNDS["width"] = half_width
            WINDOW_BOUNDS["height"] = screen_height
    except Exception as e:
        print(f"      [!] Failed to resize window: {e}")

def main_loop():
    # Change the console window title to something generic to avoid detection
    ctypes.windll.kernel32.SetConsoleTitleW("Windows System Diagnostics")
    
    global BOT_STATE
    BOT_STATE = "running"
    setup_mqtt()
    snap_window_to_right()
    
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
        
        if BOT_STATE == "paused":
            print(f"[{time.strftime('%H:%M:%S')}] Bot is paused via remote control. Waiting...", end='\r')
            time.sleep(2)
            continue
        elif BOT_STATE == "stopped":
            print("\n[!] Bot was stopped via remote control. Exiting...")
            sys.exit(0)
            
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

        # Check for out-of-stamina popup
        stamina_empty_path = os.path.join(TEMPLATE_DIR, 'stamina_empty.jpg')
        if os.path.exists(stamina_empty_path) and is_ui_present(stamina_empty_path, threshold=0.7, timeout=1.0, crop_right_half=False):
             print("      [!] Stamina empty detected! Sending alert and exiting...")
             send_ntfy_alert("Out of stamina! 💤 Bot has stopped. Please refill stamina and restart.")
             sys.exit(0)

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
    config_target = None
    clicker_mode = False
    click_rate = 50.0  # Default to 50 clicks per second

    for arg in sys.argv:
        if arg.startswith('--config-run='):
            config_target = arg.split('=')[1]
        elif arg == '--clicker':
            clicker_mode = True
        elif arg.startswith('--clicker='):
            clicker_mode = True
            try:
                click_rate = float(arg.split('=')[1])
            except ValueError:
                print(f"[!] Invalid click rate '{arg}'. Using default: {click_rate}")
            
    if clicker_mode:
        print("\n" + "=" * 50)
        print(f"Button Clicker Mode Running... ({click_rate} clicks/sec)")
        print("Move the mouse manually. The bot will auto-click.")
        print("Press 'q' or Alt-Tab and Ctrl+C in this terminal to stop.")
        print("=" * 50 + "\n")
        
        sleep_time = 1.0 / click_rate if click_rate > 0 else 0.02
        try:
            while True:
                check_kill_switch()
                pyautogui.click()
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n[!] Exiting Clicker Mode...")
            sys.exit(0)

    if '--config-run' in sys.argv or config_target:
        import configurator
        configurator.run_calibration(target_key=config_target)
        print("[*] Configuration complete. Please run the bot again!")
        sys.exit(0)
    elif not os.path.exists(CONFIG_FILE):
        print("[*] Initial setup detected. Launching configuration flow...")
        import configurator
        configurator.run_calibration()
        print("[*] Configuration complete. Please run the bot again!")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] != '--config-run':
        try:
            SQUAD_LIMIT = int(sys.argv[1])
        except ValueError:
            print(f"[!] Invalid squad limit '{sys.argv[1]}'. Using default: {SQUAD_LIMIT}")
            
    pyautogui.FAILSAFE = True
    main_loop()
