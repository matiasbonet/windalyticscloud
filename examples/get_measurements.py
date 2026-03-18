# coding: utf-8

"""
Example:
Login and request historical measurements for one station.
"""
import os
import json
from windalytics_client import WindalyticsClient


if __name__ == "__main__":
    BASE_URL = "https://easytrain.oceandrivers.com"
    EMAIL = "user@example.com" or os.getenv("WINDALYTICS_EMAIL")    
    PASSWORD = "your_password" or os.getenv("WINDALYTICS_PASSWORD")
    STATION_ID = "station_001" or os.getenv("WINDALYTICS_STATION_ID")

    client = WindalyticsClient(base_url=BASE_URL)

    client.login(EMAIL, PASSWORD)

    data = client.get_station_measurements(
        STATION_ID,
        output="json",
        limit="10",
    )

    print("\n--- LAST MEASUREMENTS ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))