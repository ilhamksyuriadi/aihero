"""
Launcher script for the Streamlit app.

This script helps run the Streamlit app with the correct module path.
Run with: uv run python run_streamlit.py
"""

import subprocess
import sys
from pathlib import Path

# Get the path to the streamlit app
app_path = Path(__file__).parent / "app" / "streamlit_app.py"

print("🚀 Starting Streamlit app...")
print(f"📁 App location: {app_path}")
print("\n" + "="*60)
print("The app will open in your browser automatically.")
print("Press Ctrl+C to stop the server.")
print("="*60 + "\n")

# Run streamlit
subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    str(app_path),
    "--server.headless", "false"
])
