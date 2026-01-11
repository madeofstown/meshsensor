#!/usr/bin/env python3
"""
Integration test for MeshSensor frontend and backend.
Tests that the frontend can properly communicate with the backend API.
"""

import sys
import json
import requests
from datetime import datetime, timezone

def test_backend():
    """Test backend API connectivity and endpoints."""
    
    print("=" * 70)
    print("MeshSensor Frontend-Backend Integration Test")
    print("=" * 70)
    print()
    
    base_url = "http://localhost:5001"
    
    # Test 1: Health check
    print("Test 1: Backend Health Check")
    print("-" * 70)
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Radio connected: {data.get('radio_connected')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {base_url}")
        print("   Make sure listener_service.py is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print()
    
    # Test 2: Get nodes
    print("Test 2: Get Nodes")
    print("-" * 70)
    try:
        response = requests.get(f"{base_url}/api/nodes", timeout=5)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            print(f"✅ Retrieved {len(nodes)} nodes")
            for node in nodes:
                print(f"   - {node.get('shortName')}: {node.get('nodeID')}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print()
    
    # Test 3: Get legacy data format
    print("Test 3: Legacy API (/data) - Used by Frontend")
    print("-" * 70)
    try:
        response = requests.get(f"{base_url}/data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            print(f"✅ Legacy endpoint works")
            print(f"   Nodes in response: {len(nodes)}")
            
            # Verify data structure
            if nodes:
                first_node = nodes[0]
                print(f"   Sample node fields:")
                print(f"   - nodeID: {first_node.get('nodeID')}")
                print(f"   - longName: {first_node.get('longName')}")
                print(f"   - telemetry records: {len(first_node.get('telemetry', []))}")
                
                # Check timestamp format in first telemetry record
                telemetry = first_node.get('telemetry', [])
                if telemetry:
                    first_tel = telemetry[0]
                    ts = first_tel.get('timestamp')
                    print(f"   - Sample timestamp format: {ts}")
                    
                    # Verify it's ISO 8601 format
                    try:
                        datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        print(f"   ✓ Timestamp is valid ISO 8601")
                    except:
                        print(f"   ✗ Timestamp is not ISO 8601 format")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print()
    
    # Test 4: Get latest telemetry
    print("Test 4: Get Latest Telemetry")
    print("-" * 70)
    try:
        response = requests.get(f"{base_url}/api/telemetry/latest", timeout=5)
        if response.status_code == 200:
            data = response.json()
            readings = data.get("data", [])
            print(f"✅ Retrieved latest from {len(readings)} nodes")
            for item in readings[:2]:  # Show first 2
                node = item.get("node", {})
                latest = item.get("latest", {})
                temp = latest.get("environmentMetrics", {}).get("temperature")
                humidity = latest.get("environmentMetrics", {}).get("relativeHumidity")
                print(f"   - {node.get('shortName')}: {temp}°F, {humidity}% humidity")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print()
    
    # Test 5: Database stats
    print("Test 5: Database Statistics")
    print("-" * 70)
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database stats:")
            print(f"   - Nodes: {data.get('nodes')}")
            print(f"   - Telemetry records: {data.get('telemetry_records')}")
            print(f"   - Oldest: {data.get('oldest_record')}")
            print(f"   - Newest: {data.get('newest_record')}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print()
    
    print("=" * 70)
    print("✅ All integration tests passed!")
    print("=" * 70)
    print()
    print("Frontend should work correctly with the backend.")
    print("Access dashboard at: http://localhost:5000")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_backend()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
