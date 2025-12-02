"""
Run Flask app with public ngrok URL
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_with_ngrok():
    from pyngrok import ngrok
    
    # Start ngrok tunnel
    print("\n" + "="*60)
    print("🚀 Starting public tunnel...")
    print("="*60 + "\n")
    
    # Create tunnel to port 5000
    public_url = ngrok.connect(5000)
    
    print("\n" + "="*60)
    print("🌐 YOUR PUBLIC LINK IS READY!")
    print("="*60)
    print(f"\n📎 Public URL: {public_url}")
    print(f"\n🔗 Share this link with anyone to access your app!")
    print("\n⚠️  Keep this terminal running to maintain the link")
    print("="*60 + "\n")
    
    # Now run the Flask app
    os.chdir(str(PROJECT_ROOT / 'web'))
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    run_with_ngrok()
