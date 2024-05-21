import subprocess
import time
import signal

# Define the command and arguments
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
args = "--remote-debugging-port=9222 --user-data-dir=/Users/xuchen/Desktop/Python_code/ChromeProfile"

# Full command to execute
command = f'"{chrome_path}" {args}'

# Loop 20 times
for i in range(20):
    print(f"Starting Chrome instance {i+1}/20")

    # Start Chrome
    proc = subprocess.Popen(command, shell=True)

    # Wait for some time (e.g., 10 seconds) before killing the process
    # Adjust the sleep time as per your requirement
    time.sleep(10)

    # Kill the process
    # On macOS and Linux, SIGTERM is generally used for graceful termination
    proc.terminate()

    # Wait for the process to terminate
    proc.wait()

    print(f"Chrome instance {i+1}/20 terminated")

    # Optional: wait for a moment before restarting the process
    time.sleep(1)

print("Completed all 20 iterations.")
