import cv2
import numpy as np
import os
import pygetwindow as gw
import ctypes
import mss
import configparser
import time

def setup_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def run_calibration(target_key=None):
    print("\n" + "="*50)
    print("🤖 ZOMBIE BOT CONFIGURATOR 🤖")
    print("="*50)
    
    setup_dpi()
    
    windows = gw.getWindowsWithTitle('Last War-Survival Game')
    if not windows:
        print("[!] Could not find the game window 'Last War-Survival Game'.")
        print("[!] Please make sure the game is running and try again.")
        return False
        
    win = windows[0]
    print(f"[*] Found game window at Logical L:{win.left}, T:{win.top}, W:{win.width}, H:{win.height}")
    
    # Try to bring to front, ignore errors if it fails
    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception:
        pass
        
    # Ensure local_config directories exist
    os.makedirs(os.path.join("local_config", "templates"), exist_ok=True)
    
    templates_to_configure = {
        'events_button': 'Events Button (usually top right menu)',
        'search': 'Search Button (rectangular button)',
        'attack_button': 'Attack Button (after clicking a zombie)',
        'march_button': 'March/Send Squad Button',
        'quit_game_menu': 'Quit Game Menu (press ESC in game first to show it, or skip if not visible)',
        'go_status': 'Just the small "Go" or "Marching" BUTTON itself (do NOT select the whole area)',
        'stamina_empty': 'Stamina Empty / Use Stamina Item popup button'
    }
    
    if target_key and target_key in templates_to_configure:
        keys_to_run = [target_key]
    else:
        keys_to_run = list(templates_to_configure.keys())
    
    print("\n" + "-"*50)
    print("INSTRUCTIONS:")
    print("Because game screens change, we will capture a fresh screenshot for each button.")
    print("1. Navigate the game so the requested button is visible.")
    print("2. Come back to this console and press ENTER to capture the screen.")
    print("   - Type 's' and press ENTER to SKIP the current button.")
    print("   - Type 'c' and press ENTER to CANCEL the entire setup.")
    print("3. In the pop-up window, drag a box closely around the button and press ENTER.")
    print("4. Press 'c' in the pop-up to skip that specific button.")
    print("-" * 50 + "\n")
    
    for key in keys_to_run:
        desc = templates_to_configure[key]
        print(f"\n>>> Please navigate to a screen showing: {desc}")
        user_input = input(">>> Press ENTER when ready to capture ('s'=skip, 'c'=cancel): ").strip().lower()
        
        if user_input == 's' or user_input == 'skip':
            print(f"    [-] Skipped {key}")
            continue
        elif user_input == 'c' or user_input == 'cancel':
            print("\n[-] Setup cancelled by user.")
            return False

        # Try to activate the window before capturing
        try:
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.5) # Give it a moment to render
        except Exception:
            pass
            
        with mss.mss() as sct:
            monitor = {
                "left": win.left,
                "top": win.top,
                "width": win.width,
                "height": win.height
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        cv2.namedWindow("Configurator", cv2.WINDOW_NORMAL)
        display_img = img.copy()
        cv2.putText(display_img, f"Select: {key}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        cv2.putText(display_img, "Drag box, then press ENTER. Press 'c' to skip.", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        
        roi = cv2.selectROI("Configurator", display_img, showCrosshair=True, fromCenter=False)
        x, y, w, h = roi
        
        if w > 0 and h > 0:
            # Crop from the ORIGINAL image without the text overlay
            crop = img[y:y+h, x:x+w]
            save_path = os.path.join("local_config", "templates", f"{key}.jpg")
            cv2.imwrite(save_path, crop)
            print(f"    [+] Saved {key}.jpg ({w}x{h})")
        else:
            print(f"    [-] Skipped {key}")
            
        cv2.destroyAllWindows()
    
    # Save config.ini
    config = configparser.ConfigParser()
    config['Window'] = {
        'left': str(win.left),
        'top': str(win.top),
        'width': str(win.width),
        'height': str(win.height)
    }
    config['Config'] = {
        'calibrated': 'true'
    }
    
    with open(os.path.join("local_config", "config.ini"), 'w') as f:
        config.write(f)
        
    print("\n" + "="*50)
    print("✅ Configuration Complete!")
    print("Your custom templates and window settings have been saved to local_config/")
    print("="*50 + "\n")
    return True

if __name__ == '__main__':
    run_calibration()
