import subprocess
import time
import sys

def keep_awake():
    if sys.platform != "darwin":
        print("❌ This script is designated for macOS only.")
        return

    print("="*40)
    print("☕ STAY AWAKE UTILITY ACTIVATED")
    print("="*40)
    print("Status: Preventing system and display sleep...")
    print("Action: Press Ctrl+C to allow the Mac to sleep again.")
    print("="*40)

    try:
        # -i: prevent system sleep, -d: prevent display sleep
        process = subprocess.Popen(['caffeinate', '-id'])
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[System] ☕ Deactivating Stay Awake utility...")
        process.terminate()
        print("[System] Success. Your Mac can now sleep normally.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    keep_awake()
