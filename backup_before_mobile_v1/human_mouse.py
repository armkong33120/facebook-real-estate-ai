
import CoreFoundation
import Quartz
import time
import math
import random

def move_mouse_human_like(x, y):
    # Get current mouse position
    cur_pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    start_x, start_y = cur_pos.x, cur_pos.y
    
    steps = 20
    for i in range(steps + 1):
        # Calculate intermediate position with a bit of randomness (curved path)
        t = i / steps
        # Simple easing
        t = t * t * (3 - 2 * t)
        
        target_x = start_x + (x - start_x) * t + random.uniform(-2, 2)
        target_y = start_y + (y - start_y) * t + random.uniform(-2, 2)
        
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, Quartz.CGPoint(target_x, target_y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        time.sleep(0.01)

if __name__ == "__main__":
    # Test: Move mouse to center of screen area (e.g., 500, 500)
    print("Moving mouse human-like to (500, 500)...")
    move_mouse_human_like(500, 500)
    print("Done.")
