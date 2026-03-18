# coding: utf-8

"""
Example:
Login and request historical measurements for one station.
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
    STATION_ID = os.getenv("WINDALYTICS_STATION_ID", "b827eb4ff7f4")
    client = WindalyticsClient(base_url=BASE_URL)

    client.login(EMAIL, PASSWORD)

    data = client.get_station_measurements(
        STATION_ID,
        output="json",
        limit="10",
    )

    print("\n--- LAST MEASUREMENTS ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))