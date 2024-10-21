import requests
import json
import time
from datetime import datetime

def fetch_tip_floor():
    url = "http://bundles-api-rest.jito.wtf/api/v1/bundles/tip_floor"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def main():
    while True:
        timestamp = datetime.now().isoformat()
        data = fetch_tip_floor()
        
        if data:
            print(f"Data fetched at {timestamp}:")
            print(json.dumps(data, indent=2))
            
            # Save to file
            with open('jito_fee_data_rest.jsonl', 'a') as f:
                json.dump({'timestamp': timestamp, 'data': data}, f)
                f.write('\n')
        else:
            print(f"Failed to fetch data at {timestamp}")
        
        # Wait for 60 seconds before the next request
        time.sleep(60)

if __name__ == "__main__":
    main()
