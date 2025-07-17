#!/usr/bin/env python3
"""
Test script to verify the analytics dashboard functionality
"""
import requests
import json

BASE_URL = "http://localhost:8050"

def test_analytics_page():
    """Test if the analytics page loads"""
    try:
        response = requests.get(f"{BASE_URL}/production/analytics/")
        print(f"✅ Analytics page: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Analytics page failed: {e}")
        return False

def test_api_endpoints():
    """Test all analytics API endpoints"""
    endpoints = [
        "dashboard_summary",
        "process_duration", 
        "plan_vs_actual",
        "worker_productivity",
        "process_trend"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/production/api/analytics/{endpoint}/")
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "✅ SUCCESS",
                    "data_count": len(data) if isinstance(data, list) else 1,
                    "sample": data[:2] if isinstance(data, list) and len(data) > 0 else data
                }
                print(f"✅ {endpoint}: {response.status_code} - {len(data) if isinstance(data, list) else 1} items")
            else:
                results[endpoint] = {
                    "status": f"❌ FAILED: {response.status_code}",
                    "error": response.text
                }
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            results[endpoint] = {
                "status": f"❌ ERROR: {str(e)}"
            }
            print(f"❌ {endpoint}: {str(e)}")
    
    return results

def main():
    print("🔍 Testing Analytics Dashboard Functionality")
    print("=" * 50)
    
    # Test analytics page
    page_working = test_analytics_page()
    
    print("\n🔍 Testing API Endpoints")
    print("-" * 30)
    
    # Test API endpoints
    api_results = test_api_endpoints()
    
    print("\n📊 Summary")
    print("-" * 30)
    print(f"Analytics page: {'✅ Working' if page_working else '❌ Failed'}")
    
    working_apis = sum(1 for result in api_results.values() if "SUCCESS" in result.get("status", ""))
    total_apis = len(api_results)
    print(f"API endpoints: {working_apis}/{total_apis} working")
    
    if working_apis == total_apis and page_working:
        print("\n🎉 All analytics functionality is working correctly!")
        return True
    else:
        print(f"\n⚠️  Some issues found. Check the details above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)