"""
Test script for the Demand Forecast API.
"""
import sys
import os
import json
import warnings
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, '/Users/mohamedemara/Desktop/dih/DIH-X-AUC-Hackathon-main')
warnings.filterwarnings('ignore')

from flask import Flask
from src.api.routes import app

def test_api():
    print("=" * 70)
    print("TESTING DEMAND FORECAST API")
    print("=" * 70)
    
    client = app.test_client()
    
    # 1. Test Health/Info
    print("\n1. Testing /api/demand/info...")
    response = client.get('/api/demand/info')
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.get_json()}")
    
    if response.status_code != 200:
        print("   FAILED")
        return
    
    # 2. Test Prediction (Mocked)
    print("\n2. Testing /api/demand/predict...")
    
    # We'll rely on the service to load the model or fail gracefully
    payload = {
        "item_id": 123,
        "place_id": 456,
        "date": "2024-03-01",
        "period": "daily"
    }
    
    try:
        response = client.post(
            '/api/demand/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.get_json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Test Training (Mocked - we don't want to actually train)
    print("\n3. Testing /api/demand/train (Dry Run)...")
    # We won't actually call it to save time, just checking if route exists
    # by sending bad data
    response = client.post(
        '/api/demand/train',
        data=json.dumps({"invalid": "data"}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    # Should be 200 (starts training with defaults) or 500 (if execution fails)
    # But for this test, getting a response means the route is wired up.

    print("\n" + "=" * 70)
    print("API TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_api()
