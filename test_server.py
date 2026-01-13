"""Test script to verify the server works properly"""
import requests
import time
import subprocess
import sys
import threading

def consume_output(pipe, name):
    """Continuously consume output from a pipe"""
    for line in iter(pipe.readline, ''):
        print(f"[{name}] {line}", end='')

print("Starting waypoint app...")
proc = subprocess.Popen([sys.executable, "app.py"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE,
                       text=True,
                       bufsize=1)

# Start threads to consume output so pipes don't block
threading.Thread(target=consume_output, args=(proc.stdout, "STDOUT"), daemon=True).start()
threading.Thread(target=consume_output, args=(proc.stderr, "STDERR"), daemon=True).start()

# Give server time to start
print("Waiting for server to start...")
time.sleep(5)

try:
    print("\nTesting http://127.0.0.1:5000/...")
    response = requests.get("http://127.0.0.1:5000/", timeout=5)
    print(f"✅ STATUS CODE: {response.status_code}")
    print(f"✅ CONTENT LENGTH: {len(response.content)} bytes")
    print(f"✅ CONTENT TYPE: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        print("\n✅ SERVER IS WORKING!")
        # Check if it's HTML
        if b'<!DOCTYPE html>' in response.content[:200]:
            print("✅ HTML content detected")
            print("✅ Title found:", b'<title>' in response.content)
        else:
            print("❌ Not HTML content")
            print("First 500 chars:", response.content[:500])
    else:
        print(f"\n❌ ERROR: Got status {response.status_code}")
        print("Response:", response.text[:500])
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\nStopping server...")
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()
    print("Server stopped")
