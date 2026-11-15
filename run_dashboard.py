"""
AI Content Factory - Dashboard Runner
Launches the FastAPI Command Center server.
"""

import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("=" * 65)
    print("🚀 AI Content Factory - Web Command Center & Dashboard")
    print("📍 Local URL: http://127.0.0.1:8000")
    print("⚡ Real-time automation control, idea generator & analytics")
    print("=" * 65)
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
