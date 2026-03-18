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
    """
    print("\n--- NEW REAL-TIME DATA RECEIVED ---")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


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