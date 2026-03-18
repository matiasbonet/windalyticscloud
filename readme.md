# Windalytics Python Client

Python client for authenticating against the Windalytics REST API and consuming real-time data from the Socket.IO server.

## Features

- Login using email and password
- Store and reuse the access token
- Connect to the Socket.IO stream
- Receive `stream_data` events in real time
- Call protected REST endpoints
- Example scripts for common use cases

## Project structure

```text
windalytics_client/
│
├── windalytics_client/
│   ├── __init__.py
│   └── client.py
│
├── examples/
│   ├── login_and_stream.py
│   ├── list_stations.py
│   └── get_measurements.py
│
└── requirements.txt
```

## Requirements

```txt
python-socketio==5.16.1
python-engineio==4.13.1
requests==2.32.5
websocket-client>=1.8.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Server compatibility

This client is intended for a backend using:

- Flask-SocketIO 5.x
- python-socketio 5.x
- REST API under `/api`
- Socket.IO server attached to the Flask app root

That means:

- REST base URL: `https://your-server.com/api`
- Socket.IO base URL: `https://your-server.com`

## Authentication

The login endpoint is:

```http
POST /api/auth/login/
Content-Type: application/json
```

Request body:

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

After login, the client stores the returned token and uses it in two ways:

1. For REST requests, through the `Authorization` header
2. For Socket.IO subscriptions, by emitting the `join` event with the token

## How the real-time subscription works

After connecting to Socket.IO, the client emits:

```python
sio.emit("join", token)
```

The backend then adds the client to the rooms associated with the stations allowed by that token. Once subscribed, the client receives:

```python
stream_data
```

## Main client class

```python
from windalytics_client import WindalyticsClient

client = WindalyticsClient(
    base_url="http://127.0.0.1:5000"
)
```

### Constructor parameters

- `base_url`: server base URL, for example `http://127.0.0.1:5000`
- `token`: optional existing token
- `mac`: optional `MAC` header for Socket.IO connection
- `log_level`: logging level such as `INFO` or `DEBUG`

## Basic example: login and listen to real-time data

```python
import json
from windalytics_client import WindalyticsClient


def handle_stream_data(payload):
    print("\n--- NEW REAL-TIME DATA RECEIVED ---")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


client = WindalyticsClient(base_url="http://127.0.0.1:5000")
client.login("user@example.com", "your_password")
client.set_stream_handler(handle_stream_data)
client.connect_socket()
client.wait_forever()
```

## List available stations

```python
import json
from windalytics_client import WindalyticsClient

client = WindalyticsClient(base_url="http://127.0.0.1:5000")
client.login("user@example.com", "your_password")

stations = client.get_stations()
print(json.dumps(stations, indent=2, ensure_ascii=False))
```

## Request historical measurements

```python
import json
from windalytics_client import WindalyticsClient

client = WindalyticsClient(base_url="http://127.0.0.1:5000")
client.login("user@example.com", "your_password")

data = client.get_station_measurements(
    "station_001",
    output="json",
    limit="10"
)

print(json.dumps(data, indent=2, ensure_ascii=False))
```

## Public methods

### `login(email, password, timeout=10)`

Authenticates against the REST API and stores the token.

### `logout(timeout=10)`

Logs out through the REST API.

### `get_stations(timeout=10)`

Returns the list of stations available to the authenticated user.

### `get_station_measurements(...)`

Requests historical measurements for one station using the endpoint:

```http
GET /api/easywind_data_operations/{station_id}/getmeasurements
```

### `set_stream_handler(callback)`

Replaces the default `stream_data` event handler.

### `connect_socket(wait_timeout=10)`

Connects to the Socket.IO server.

### `wait_forever()`

Keeps the client running and listening for events.

### `disconnect_socket()`

Disconnects the Socket.IO connection.

## Example `stream_data` payload

The backend emits data in this shape:

```json
{
  "data": {
    "unit_mac": "AA:BB:CC:DD:EE:FF",
    "station_name": "My Station",
    "station_id": "station_001",
    "station_code": "ABC123",
    "station_timezone": "Europe/Madrid",
    "data": {
      "data": {
        "mean_data": "{...}",
        "raw_data": {
          "windappangle": 32.1,
          "windappspeed": 14.5
        }
      }
    }
  }
}
```

Depending on your backend implementation, `mean_data` may be a JSON string that should be parsed before use.

## Notes about authorization format

The Swagger definition uses `Authorization` header with Bearer auth. The client currently sends:

```http
Authorization: Bearer <token>
```

If your backend expects only the raw token, update the header generation in the client.

## Troubleshooting

### Login works but token is not detected

Your Swagger file defines the login request but not the exact response body. If the server returns the token under a custom field, update the token extraction logic in the client.

### REST works but Socket.IO does not receive data

Check the following:

- The client is connecting to the base server URL, not to `/api`
- The token used in `join` is valid
- The user has permission to access at least one station
- The backend is emitting `stream_data` events for the associated station rooms

### Connection issues behind proxy

If you deploy behind Nginx or another reverse proxy, verify WebSocket upgrade headers are enabled.

## Minimal usage

```python
from windalytics_client import WindalyticsClient

client = WindalyticsClient("http://127.0.0.1:5000")
client.login("user@example.com", "password")
client.connect_socket()
client.wait_forever()
```

## License

Add your license here if you plan to distribute the client externally.

