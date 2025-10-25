"""
Simple runner script for the Expense Tracker API.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Now we can import the app
from packages.api.src.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Expense Tracker API")
    print("=" * 60)
    print(f"📍 Server: http://localhost:5000")
    print(f"📍 Health check: http://localhost:5000/health")
    print(f"📍 Project root: {project_root}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host="0.0.0.0", port=5000)
