# Filename: create_production_plans_via_api.py
#
# How to run this script:
# 1. Ensure your Django project is running and the API endpoint for ProductionPlan is available.
# 2. Make sure you have the 'requests' library installed: pip install requests
# 3. Run this script from your terminal: python create_production_plans_via_api.py
#
# This script assumes your API is running at API_BASE_URL (e.g., http://127.0.0.1:8000/api)

import requests
from datetime import datetime, timezone
import json # For pretty printing JSON responses
import configparser
import os

API_BASE_URL = "http://127.0.0.1:8000/api" # Adjust if your API base URL is different
# Corrected endpoint based on urls.py: /api/production/plans/
PRODUCTION_PLANS_ENDPOINT = f"{API_BASE_URL}/production/plans/"

# --- Load API Token from config.ini ---
API_TOKEN = None
try:
    config = configparser.ConfigParser()
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config.read(config_path)
    API_TOKEN = config.get('API', 'TOKEN', fallback=None)
except Exception as e:
    print(f"Warning: Could not read API token from config.ini. Error: {e}")

# Optional: If your API requires authentication, set up headers here
HEADERS = {
    "Content-Type": "application/json",
}
if API_TOKEN:
    HEADERS["Authorization"] = f"Token {API_TOKEN}"
else:
    print("Warning: API_TOKEN is not set. Requests will be made without authentication.")

def create_main_plan_via_api():
    """
    Demonstrates creating a top-level production plan via API.
    Returns the ID of the created plan if successful, otherwise None.
    """
    print("--- Attempting to create a main production plan via API ---")
    if not API_TOKEN:
        print("Error: API Token not found. Cannot proceed with authenticated request.")
        return None

    payload = {
        'plan_name': 'Q4 Major Assembly (API)',
        'product_code': 'PROD-API-001',
        'production_plan': None,  # None for a top-level plan
        'planned_quantity': 6000,
        'planned_start_datetime': datetime(2025, 1, 10, 8, 0, 0, tzinfo=timezone.utc).isoformat(),
        'planned_end_datetime': datetime(2025, 3, 25, 17, 0, 0, tzinfo=timezone.utc).isoformat(),
        'remarks': 'Main assembly plan for Q1 2025, created via API.'
        # actual_start_datetime and actual_end_datetime are omitted
        # status, id, created_at, updated_at are handled by the API
    }

    try:
        response = requests.post(PRODUCTION_PLANS_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        if response.status_code == 201: # Created
            created_plan_data = response.json()
            print("Successfully created main plan via API:")
            print(f"  Response JSON: {json.dumps(created_plan_data, indent=2)}")
            print(f"  ID: {created_plan_data.get('id')}")
            print(f"  Name: {created_plan_data.get('plan_name')}")
            print(f"  Status: {created_plan_data.get('status')}")
            return created_plan_data.get('id')
        else:
            print(f"Failed to create main plan. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content.decode()}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def create_sub_plan_via_api(parent_plan_id):
    """
    Demonstrates creating a sub-production plan linked to a parent plan via API.
    """
    if not parent_plan_id:
        print("Parent plan ID is required to create a sub-plan.")
        return None
    
    if not API_TOKEN:
        print("Error: API Token not found. Cannot proceed with authenticated request.")
        return None

    print(f"\n--- Attempting to create a sub-plan via API for parent ID: {parent_plan_id} ---")
    payload = {
        'plan_name': 'January Phase 1 (Sub-plan API)',
        'product_code': 'PROD-API-001-SUB',
        'production_plan': parent_plan_id,  # Link to the parent plan's ID
        'planned_quantity': 2000,
        'planned_start_datetime': datetime(2025, 1, 10, 8, 0, 0, tzinfo=timezone.utc).isoformat(),
        'planned_end_datetime': datetime(2025, 1, 31, 17, 0, 0, tzinfo=timezone.utc).isoformat(),
        'remarks': 'First phase sub-plan for January, created via API.'
    }

    try:
        response = requests.post(PRODUCTION_PLANS_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()

        if response.status_code == 201:
            created_sub_plan_data = response.json()
            print("Successfully created sub-plan via API:")
            print(f"  Response JSON: {json.dumps(created_sub_plan_data, indent=2)}")
            print(f"  ID: {created_sub_plan_data.get('id')}")
            print(f"  Name: {created_sub_plan_data.get('plan_name')}")
            print(f"  Parent Plan ID: {created_sub_plan_data.get('production_plan')}")
            return created_sub_plan_data.get('id')
        else:
            print(f"Failed to create sub-plan. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content.decode()}")
        try:
            # Attempt to print JSON error details if available
            error_details = response.json()
            print(f"Error details: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            pass # No JSON in error response
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def create_invalid_plan_via_api():
    """
    Demonstrates attempting to create a plan with invalid dates via API (should fail).
    """
    print("\n--- Attempting to create a plan with invalid dates via API (should fail) ---")
    if not API_TOKEN:
        print("Error: API Token not found. Cannot proceed with authenticated request.")
        return None

    payload = {
        'plan_name': 'Invalid Date Plan (API)',
        'product_code': 'ERR-API-001',
        'planned_quantity': 100,
        'planned_start_datetime': datetime(2025, 2, 15, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
        'planned_end_datetime': datetime(2025, 2, 20, 17, 0, 0, tzinfo=timezone.utc).isoformat(), # End is before start
        'remarks': 'This plan should fail validation due to incorrect dates (API).'
    }

    try:
        response = requests.post(PRODUCTION_PLANS_ENDPOINT, json=payload, headers=HEADERS)

        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 400: # Bad Request (expected for validation error)
            print("API reported invalid data as expected. Error response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
                # If you used the suggested serializer change, the error might be like:
                # { "planned_end_datetime": ["Planned end datetime must be after planned start datetime."] }
            except json.JSONDecodeError:
                print(response.text) # Print raw text if not JSON
        elif response.status_code >= 200 and response.status_code < 300:
            print("Data was unexpectedly valid by API. This should not happen.")
            print(f"Response: {response.json()}")
        else:
            print(f"Received unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.HTTPError as http_err:
        # This might catch 400 if raise_for_status() was called before checking status_code
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content.decode()}")
        try:
            error_details = response.json()
            print(f"Error details: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            pass
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    print("Starting production plan creation script via API.")
    print(f"Target API: {PRODUCTION_PLANS_ENDPOINT}")
    print("Ensure your Django development server is running and the API is accessible.\n")

    # 1. Create a main plan
    parent_id = create_main_plan_via_api()

    # 2. If main plan created, create a sub-plan
    if parent_id:
        create_sub_plan_via_api(parent_id)
    else:
        print("\nSkipping sub-plan creation as main plan creation failed or returned no ID.")

    # 3. Test invalid plan creation
    create_invalid_plan_via_api()

    print("\nScript example finished.")
