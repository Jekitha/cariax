"""
CARIAX Public Link Launcher
Automatically starts the app and creates a public URL
"""

import subprocess
import sys
import os
import time
import re
import webbrowser

def main():
    print("=" * 60)
    print("🚀 CARIAX - Starting Public Server")
    print("=" * 60)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(script_dir, "web")
    
    # Start Flask app
    print("\n⏳ Starting Flask server...")
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=web_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Check if Flask started successfully
    if flask_process.poll() is not None:
        print("❌ Flask server failed to start!")
        return
    
    print("✅ Flask server running on http://localhost:5000")
    
    # Start Cloudflare tunnel
    print("\n⏳ Creating public tunnel...")
    
    # Find cloudflared
    cloudflared_paths = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
        "cloudflared"
    ]
    
    cloudflared_path = None
    for path in cloudflared_paths:
        if os.path.exists(path) or path == "cloudflared":
            cloudflared_path = path
            break
    
    if not cloudflared_path:
        print("❌ Cloudflared not found! Please install it.")
        print("   Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        flask_process.terminate()
        return
    
    # Start tunnel
    tunnel_process = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for tunnel URL
    public_url = None
    print("\n⏳ Waiting for public URL...")
    
    start_time = time.time()
    while time.time() - start_time < 30:  # 30 second timeout
        line = tunnel_process.stdout.readline()
        if line:
            # Look for the URL in the output
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                public_url = match.group(0)
                break
    
    if public_url:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Your app is now PUBLIC!")
        print("=" * 60)
        print(f"\n🌐 PUBLIC URL: {public_url}")
        print("\n📋 Copy this link and share it on LinkedIn!")
        print("\n⚠️  Keep this window open to keep the link active.")
        print("    Press Ctrl+C to stop the server.\n")
        print("=" * 60)
        
        # Open in browser
        webbrowser.open(public_url)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                if flask_process.poll() is not None:
                    print("❌ Flask server stopped!")
                    break
                if tunnel_process.poll() is not None:
                    print("❌ Tunnel stopped!")
                    break
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
    else:
        print("❌ Failed to create tunnel!")
    
    # Cleanup
    flask_process.terminate()
    tunnel_process.terminate()
    print("✅ Server stopped.")

if __name__ == "__main__":
    main()
