import os
import json
import datetime
from sendgrid import SendGridAPIClient
from google.cloud import bigquery
from datetime import date
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
TABLE_ID = os.getenv("TABLE_ID")
TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

sg = SendGridAPIClient(SENDGRID_API_KEY)

def get_parent_stats(start_date, aggregated_by='month'):
    """Retrieves high-level global usage statistics for the parent account."""
    params = {
        'start_date': start_date,
        'aggregated_by': aggregated_by
    }
    try:
        response = sg.client.stats.get(query_params=params)
        print(f"Parent Stats Status: {response.status_code}")
        return json.loads(response.body)
    except Exception as e:
        print(f"Error fetching parent stats: {e}")
        return None

def get_all_subusers_sums(start_date):
    """Retrieves the total sum of email metrics across ALL subusers."""
    params = {
        'start_date': start_date
    }
    try:
        # Calls the /v3/subusers/stats/sums endpoint
        response = sg.client.subusers.stats.sums.get(query_params=params)
        print(f"All Subusers Sums Status: {response.status_code}")
        # return json.loads(response.body)
        return response
    except Exception as e:
        print(f"Error fetching subuser sums: {e}")
        return None


def get_specific_subuser_activity(subuser_username, limit=100):
    """Fetches granular raw message logs (Activity Feed) for a specific subuser 
    by injecting the 'On-Behalf-Of' header."""
    params = {
        'limit': limit
    }
    custom_headers = {
        'On-Behalf-Of': subuser_username
    }
    try:
        # Calls the /v3/messages endpoint on behalf of the subuser
        response = sg.client.messages.get(query_params=params, request_headers=custom_headers)
        print(f"Subuser '{subuser_username}' Activity Status: {response.status_code}")
        return json.loads(response.body)
    except Exception as e:
        print(f"Error fetching activity feed for {subuser_username}: {e}")
        return None

# --- Execution ---
if __name__ == "__main__":
    # 1. Fetch overall parent overview usage
    parent_data = get_parent_stats(start_date='2026-10-01')
    # print (json.dumps(parent_data, indent=4))

    # 2. Fetch combined metrics for all subusers
    subusers_total = get_all_subusers_sums(start_date='2026-10-01') # ->         return json.loads(response.body)
    # print (json.dumps(subusers_total, indent=4))

    # 3. Fetch granular activity logs for a specific subuser
    # (Requires the Email Activity History add-on enabled on the account)
    # subuser_logs = get_specific_subuser_activity(subuser_username='')

    bq_client = bigquery.Client()
    raw_data = subusers_total.to_dict

    rows_to_insert = []

    # Loop through SendGrid's dates array structure
    for day_entry in raw_data.get('stats', []):

        row = {
            "type": "subuser",
            "name": day_entry.get('name'),
            "requests": day_entry.get('metrics').get('requests'),
            "date": raw_data.get('date')
        }

        rows_to_insert.append(row)

    # Stream the records to BigQuery using streaming inserts
    if rows_to_insert:
        errors = bq_client.insert_rows_json(TABLE_REF, rows_to_insert)
        if errors == []:
            print(f"Successfully inserted {len(rows_to_insert)} rows into BigQuery.")
        else:
            print(f"Encountered insertion errors: {errors}")
    else:
        print("No new data to insert.")