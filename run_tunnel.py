import subprocess
import time
import re
import sys
import os

# Ensure Windows stdout handles UTF-8 emojis cleanly
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("==================================================", flush=True)
print("   🚀 STARTING CRYPTO ARBITRAGE BOT SERVER       ", flush=True)
print("==================================================\n", flush=True)

# 1. Start Python App server
app_proc = subprocess.Popen([sys.executable, "app.py"])

time.sleep(2)

print("\n🌐 Creating Secure Mobile Access Link...", flush=True)

# 2. Start Cloudflare Tunnel process
tunnel_proc = subprocess.Popen(
    ["cloudflared.exe", "tunnel", "--url", "http://localhost:5000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

mobile_url = None
try:
    for line in iter(tunnel_proc.stdout.readline, ''):
        print(line, end='', flush=True)
        if "trycloudflare.com" in line and not mobile_url:
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                mobile_url = match.group(0)
                print("\n" + "*"*60, flush=True)
                print(f"📱 YOUR LIVE MOBILE LINK: {mobile_url}", flush=True)
                print("Open this link on your Mobile Phone browser to access your Bot!", flush=True)
                print("*"*60 + "\n", flush=True)
except KeyboardInterrupt:
    print("\nShutting down...", flush=True)

app_proc.wait()
