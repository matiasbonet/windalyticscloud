# coding: utf-8

"""
Example:
1. Login through REST API
2. Receive token
3. Connect to Socket.IO
4. Listen for stream_data events
"""
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

import json
from windalytics_client import WindalyticsClient


def handle_stream_data(payload):
    """
    Custom callback for incoming real-time data.

    --- NEW REAL-TIME DATA RECEIVED ---
    {
    "data": {
        "unit_mac": "b827ebd02144",
        "data": {
            "data": {
                "mean_data": 
                    "{\"time\": 1773834775.22654, \"latitude\": 0.0, \"longitude\": 0.0, \"COG\": 0.0, \"SOG\": 0.0, \"pressure\": 1004.4, \"temperature\": 21.3, \"AWS\": 1.0, \"AWA\": 90.9, \"AWAR\": 0.0, \"heading\": 247.4, \"heading_true\": 247.9, \"pitch\": -4.2, \"rol\": -1.1, \"TWA\": -112.60000000000002, \"TWD\": 0, \"TWS\": 0.0, \"wind_u\": 0.0, \"wind_v\": 0.0}"
                ,
                "raw_data": {
                    "heading": 247.4,
                    "pressure": 1004.4,
                    "airtemperature": "21.3",
                    "pitch": -4.2,
                    "rol": -1.1,
                    "windappangle": 90.9,
                    "windappspeed": 1.0,
                    "heading_true": 247.9
                }
            }
        },
        "station_name": "EWP074",
        "station_id": "b827ebd02144",
        "station_code": "EWP074",
        "station_timezone": 0.0
    }
    }

    """
    print("\n--- NEW REAL-TIME DATA RECEIVED ---")
    #print(json.dumps(payload, indent=2, ensure_ascii=False))

    station_name = payload["data"]["station_name"]
    station_code = payload["data"]["station_code"]
    
    data = payload["data"]["data"]["data"]
    mean_data = json.loads(data["mean_data"])
    raw_data = data["raw_data"]

    print("----- REAL-TIME DATA RECEIVED -----")
    print(f"Station: {station_name} (CODE: {station_code})") 
    print(f"Mean AWS: {mean_data['AWS']}, Mean AWA: {mean_data['AWA']} ")
    print(f"Raw AWS: {raw_data['windappspeed']} , Raw AWA: {raw_data['windappangle']} ")
    print("----------------------------------")
    




if __name__ == "__main__":
    BASE_URL = os.getenv("WINDALYTICS_BASE_URL", "https://easytrain.oceandrivers.com")
    EMAIL = os.getenv("WINDALYTICS_EMAIL", "user@example.com")
    PASSWORD = os.getenv("WINDALYTICS_PASSWORD", "your_password")

    client = WindalyticsClient(
        base_url=BASE_URL,
        log_level="INFO",
    )

    # Step 1: login through REST API
    client.login(EMAIL, PASSWORD)

    # Step 2: define custom event handler
    client.set_stream_handler(handle_stream_data)

    # Step 3: connect to Socket.IO
    client.connect_socket()

    # Step 4: keep listening
    client.wait_forever()