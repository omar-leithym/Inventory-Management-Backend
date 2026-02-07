"""
Main application entry point.
"""
import sys
import os

# Ensure the project root is in the Python path
# Assuming this file is at src/main.py, project root is one level up
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.routes import app

if __name__ == "__main__":
    print(f"Starting Demand Forecast API server...")
    print(f"Project root: {project_root}")
    app.run(debug=True, host='0.0.0.0', port=5001)
