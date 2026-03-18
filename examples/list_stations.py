# coding: utf-8

"""
Example:
Login and request available stations from the REST API.
"""

import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

import json
from windalytics_client import WindalyticsClient

if __name__ == "__main__":
    BASE_URL = os.getenv("WINDALYTICS_BASE_URL", "https://easytrain.oceandrivers.com")
    EMAIL = os.getenv("WINDALYTICS_EMAIL", "user@example.com")
    PASSWORD = os.getenv("WINDALYTICS_PASSWORD", "your_password")

    client = WindalyticsClient(base_url=BASE_URL)

    client.login(EMAIL, PASSWORD)

    stations = client.get_stations()

    print("\n--- AVAILABLE STATIONS ---")
    for station in stations:
        print(f"- {station['alias']} (CODE: {station['station_code']} ID: {station['station_id']})")
