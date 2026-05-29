import cv2
import numpy as np
import mss
import os

def test_vision():
    # Setup MSS for screen capture
    sct = mss.mss()
    
    # You can change this to 2 if your game is on your secondary monitor
    # Monitors: 0 = All Monitors, 1 = Primary, 2 = Secondary, etc.
    monitor_number = 1 
    
    if monitor_number >= len(sct.monitors):
        print(f"Error: Monitor {monitor_number} not found.")
        return
        
    monitor = sct.monitors[monitor_number]
    
    # Crop to the right half of the screen for better performance
    monitor = {
        "top": monitor["top"],
        "left": monitor["left"] + (monitor["width"] // 2),
        "width": monitor["width"] // 2,
        "height": monitor["height"]
    }
    
    print(f"Capturing screen from right half of monitor {monitor_number}: {monitor}")

    # Load templates
    template_dir = os.path.join('source_images', '2026-05-28')
    templates = []
    
    if not os.path.exists(template_dir):
        print(f"Error: {template_dir} directory not found.")
        return
        
    # We will try to load all jpg files
    for filename in os.listdir(template_dir):
        if filename.endswith('.jpg'):
            path = os.path.join(template_dir, filename)
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                templates.append((filename, img))
                print(f"Loaded template: {filename}")
            else:
                print(f"Failed to load: {filename}")

    if not templates:
        print("No zombie templates found in source_images!")
        return

    print("\nStarting vision test...")
    print("Switch to your game! You should see a window pop up showing what the bot sees.")
    print("If it detects a zombie, a RED BOX will appear around it.")
    print("Make sure the game is visible on the screen.")
    print("Press 'q' on your keyboard while the image window is selected to close.")

    while True:
        # Capture screen
        screenshot = sct.grab(monitor)
        
        # Convert to numpy array and drop the alpha channel
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
        
        # We will keep a copy to draw on
        display_frame = frame.copy()
        
        # Test each template
        found_any = False
        for filename, template in templates:
            # Get template dimensions
            h, w = template.shape[:2]
            
            # Match template
            res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.60 # Lowered to 60% to debug
            
            # Find the best match regardless of threshold
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            # Draw the best match in blue to show where it THINKS the zombie is
            best_pt = max_loc
            cv2.rectangle(display_frame, best_pt, (best_pt[0] + w, best_pt[1] + h), (255, 0, 0), 2)
            cv2.putText(display_frame, f"{max_val:.2f}", (best_pt[0], best_pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            # Find all locations above the threshold (Red boxes for confirmed matches)
            loc = np.where(res >= threshold)
            
            for pt in zip(*loc[::-1]): # Switch x and y
                found_any = True
                # Draw a rectangle around the matched region
                cv2.rectangle(display_frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
                # Put the name of the template above the box
                cv2.putText(display_frame, filename, (pt[0], pt[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Because 4K/Retina screens are huge, let's resize the display window so it fits on screen nicely
        scale_percent = 50 # percent of original size
        width = int(display_frame.shape[1] * scale_percent / 100)
        height = int(display_frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        
        resized_frame = cv2.resize(display_frame, dim, interpolation=cv2.INTER_AREA)

        # Show the result in a window
        cv2.imshow('Vision Test (Resized 50%)', resized_frame)
        
        # Break loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("Test finished.")

if __name__ == '__main__':
    test_vision()
