# Filename: create_parts_used_example.py
#
# How to run this script:
# 1. Ensure your Django project is running.
# 2. Make sure you have created an API endpoint for PartsUsed.
#    (See instructions in the accompanying documentation/response).
# 3. Make sure you have the 'requests' and 'Faker' libraries installed:
#    pip install requests Faker
# 4. Run this script from your terminal: python create_parts_used_example.py
#
# This script assumes your API is running at API_BASE_URL (e.g., http://127.0.0.1:8000/api)

import requests
from datetime import datetime, timezone, timedelta
import json # For pretty printing JSON responses
import configparser
import os
from faker import Faker

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api" # Adjust if your API base URL is different
# Endpoint for ProductionPlan (to get a parent ID for PartsUsed)
PRODUCTION_PLANS_ENDPOINT = f"{API_BASE_URL}/production/plans/"
# ASSUMPTION: Endpoint for PartsUsed - YOU MUST CREATE THIS IN YOUR DJANGO APP
PARTS_USED_ENDPOINT = f"{API_BASE_URL}/production/parts-used/"

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

HEADERS = {
    "Content-Type": "application/json",
}
if API_TOKEN:
    HEADERS["Authorization"] = f"Token {API_TOKEN}"
else:
    print("Warning: API_TOKEN is not set. Requests will be made without authentication.")

fake = Faker('ja_JP') # Use Japanese locale for Faker

def create_test_production_plan():
    """
    Creates a new production plan for testing PartsUsed.
    Returns the ID of the created plan if successful, otherwise None.
    """
    print("--- Attempting to create a test production plan via API ---")
    if not API_TOKEN:
        print("Error: API Token not found. Cannot proceed with authenticated request for creating plan.")
        return None

    payload = {
        'plan_name': f'Test Plan for PartsUsed {fake.uuid4()[:8]} (API)',
        'product_code': f'PROD-API-{fake.random_number(digits=3)}',
        'production_plan': None,  # Top-level plan
        'planned_quantity': fake.random_int(min=10, max=50),
        'planned_start_datetime': datetime.now(timezone.utc).isoformat(),
        'planned_end_datetime': (datetime.now(timezone.utc) + timedelta(days=fake.random_int(min=1, max=5))).isoformat(),
        'remarks': 'Auto-created test plan for PartsUsed entries via API.'
    }

    try:
        response = requests.post(PRODUCTION_PLANS_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()

        if response.status_code == 201: # Created
            created_plan_data = response.json()
            print("Successfully created test production plan:")
            print(f"  ID: {created_plan_data.get('id')}")
            return created_plan_data.get('id')
        else:
            print(f"Failed to create test plan. Status: {response.status_code}, Response: {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while creating test plan: {http_err}")
        print(f"Response content: {http_err.response.content.decode()}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred while creating test plan: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred while creating test plan: {e}")
    return None

def create_parts_used_entry_via_api(production_plan_id):
    """
    Creates a single PartsUsed entry via API, linked to the given production_plan_id.
    """
    if not production_plan_id:
        print("Error: production_plan_id is required to create a PartsUsed entry.")
        return None
    
    if not API_TOKEN:
        print("Error: API Token not found. Cannot proceed with authenticated request for PartsUsed.")
        return None

    payload = {
        "production_plan": production_plan_id,
        "part_code": f"PART-{fake.bothify(text='???-####').upper()}", # Example: PART-ABC-1234
        "quantity_used": fake.random_int(min=1, max=100),
        "used_datetime": fake.date_time_this_year(tzinfo=timezone.utc).isoformat(), # ISO 8601 format
        "remarks": fake.sentence() if fake.boolean(chance_of_getting_true=40) else None,
    }

    print(f"\n--- Attempting to create PartsUsed entry for Production Plan ID: {production_plan_id} ---")
    # print(f"Payload: {json.dumps(payload, indent=2)}") # Uncomment for debugging payload

    try:
        response = requests.post(PARTS_USED_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        if response.status_code == 201: # Created
            created_data = response.json()
            print("Successfully created PartsUsed entry via API:")
            print(f"  Response JSON: {json.dumps(created_data, indent=2)}")
            print(f"  ID: {created_data.get('id')}")
            return created_data.get('id')
        else:
            print(f"Failed to create PartsUsed entry. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {http_err.response.content.decode()}")
        try:
            error_details = http_err.response.json() # Attempt to parse JSON error from API
            print(f"Error details: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            pass # No JSON in error response, raw content already printed
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

if __name__ == '__main__':
    print("Starting PartsUsed creation script via API.")
    print(f"Target API for PartsUsed: {PARTS_USED_ENDPOINT}")
    print("Ensure your Django development server is running and the API is accessible.")
    print(f"This script will first attempt to create a Production Plan at: {PRODUCTION_PLANS_ENDPOINT}")
    print("IMPORTANT: This script ASSUMES the PartsUsed API endpoint is available at the URL above and correctly configured in your Django urls.py.\n")

    if not API_TOKEN:
        print("Critical Error: API_TOKEN is not set. Please check your config.ini.")
        print("Script cannot proceed with authenticated requests.")
    else:
        # 1. Create a test Production Plan to associate PartsUsed entries with
        parent_plan_id = create_test_production_plan()

        if parent_plan_id:
            print(f"\nUsing Production Plan ID: {parent_plan_id} for creating PartsUsed entries.")
            num_entries_to_create = 3 # Number of PartsUsed entries to create for the plan
            for i in range(num_entries_to_create):
                print(f"\n--- Creating PartsUsed Entry {i+1}/{num_entries_to_create} ---")
                create_parts_used_entry_via_api(parent_plan_id)
        else:
            print("\nCould not create or obtain a Production Plan ID. Skipping PartsUsed creation.")

    print("\nScript example finished.")