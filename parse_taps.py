import re

def parse_getevent(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    taps = []
    curr_x = None
    curr_y = None
    
    for line in lines:
        # Match X position
        x_match = re.search(r'ABS_MT_POSITION_X\s+([0-9a-f]+)', line)
        if x_match:
            curr_x = int(x_match.group(1), 16)
        
        # Match Y position
        y_match = re.search(r'ABS_MT_POSITION_Y\s+([0-9a-f]+)', line)
        if y_match:
            curr_y = int(y_match.group(1), 16)
            
        # Match Tap Down event
        if 'BTN_TOUCH' in line and 'DOWN' in line:
            if curr_x is not None and curr_y is not None:
                taps.append((curr_x, curr_y))
                # Reset for next tap to avoid duplicate if X/Y doesn't change
                # (though usually they do)
    
    return taps

taps = parse_getevent('touch_events_v4.log')
print("--- Resulting Taps ---")
for i, (x, y) in enumerate(taps):
    print(f"Step {i+1}: adb shell input tap {x} {y}")
