# coding: utf-8

"""
Windalytics external client.

This client supports:
1. Login through the REST API
2. Token storage
3. Real-time Socket.IO connection
4. Optional authenticated REST requests

Designed for external customers who need a simple integration example.
"""

import json
import logging
from typing import Any, Callable, Optional

import requests
import socketio


class WindalyticsClient:
    """
    Client for the Windalytics platform.

    Parameters
    ----------
    base_url : str
        Server base URL, for example:
        http://127.0.0.1:5000
        https://api.example.com

    token : str | None
        Existing access token. Optional if you will call login() first.

    mac : str | None
        Optional MAC header sent during Socket.IO connection.
        Your backend reads this header on connect, but it is not required
        for standard viewer/external clients.

    log_level : str
        Logging level: DEBUG, INFO, WARNING, ERROR
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        mac: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_base_url = f"{self.base_url}/api"
        self.token = token
        self.mac = mac

        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)s | %(message)s",
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # requests session for REST API calls
        self.session = requests.Session()

        # Socket.IO client for real-time streaming
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,   # infinite retries
            reconnection_delay=2,
            reconnection_delay_max=15,
        )

        self._register_default_socket_events()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_default_socket_events(self) -> None:
        """
        Register default Socket.IO event handlers.

        External users can replace the 'stream_data' handler later with
        set_stream_handler().
        """

        @self.sio.event
        def connect() -> None:
            print(f"Connected to Socket.IO server: {self.base_url}")

            if not self.token:
                print("No token available. Please call login() first or provide a token.")
                return

            # Your backend expects the token as payload of the 'join' event.
            print("Sending join request with access token...")
            self.sio.emit("join", self.token)

        @self.sio.event
        def disconnect() -> None:
            print("Disconnected from Socket.IO server")

        @self.sio.event
        def connect_error(data: Any) -> None:
            print("Socket.IO connection error:", data)

        @self.sio.on("stream_data")
        def stream_data(payload: Any) -> None:
            """
            Default event handler for real-time data.

            This can be overridden with set_stream_handler().
            """
            print("Received stream_data event:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Build Authorization header for protected REST endpoints.

        Swagger defines Bearer Auth in the Authorization header.
        """
        print("Token ", self.token)
        if not self.token:
            raise RuntimeError("No token available. Please login first.")

        return {
            "Authorization": f"Bearer {self.token}"
        }

    def _extract_token_from_login_response(self, data: dict[str, Any]) -> str:
        """
        Try to extract the token from different possible response formats.

        Because Swagger does not define the exact login response schema,
        we support several common patterns.
        """
        possible_paths = [
            data.get("token"),
            data.get("access_token"),
            data.get("auth_token"),
            data.get("jwt"),
            data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None,
            data.get("response", {}).get("token") if isinstance(data.get("response"), dict) else None,
        ]

        token = next((value for value in possible_paths if value), None)

        if not token:
            raise ValueError(
                "Could not find token in login response. "
                f"Received response: {data}"
            )

        return token

    # ------------------------------------------------------------------
    # Public REST API methods
    # ------------------------------------------------------------------

    def login(self, email: str, password: str, timeout: int = 10) -> str:
        """
        Authenticate against the REST API and store the token.

        Endpoint from Swagger:
        POST /api/auth/login/

        Parameters
        ----------
        email : str
            User email
        password : str
            User password
        timeout : int
            Request timeout in seconds

        Returns
        -------
        str
            Access token
        """
        url = f"{self.api_base_url}/auth/login/"
        payload = {
            "email": email,
            "password": password,
        }

        print(f"Requesting token from: {url}")

        response = self.session.post(url, json=payload, timeout=timeout, verify=False )

        if response.status_code != 200:
            raise RuntimeError(
                f"Login failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        token = self._extract_token_from_login_response(data)

        self.token = token
        print("Login successful. Token received and stored.")

        return token

    def logout(self, timeout: int = 10) -> requests.Response:
        """
        Logout through the REST API.

        Endpoint from Swagger:
        POST /api/auth/logout/
        """
        url = f"{self.api_base_url}/auth/logout/"
        print(f"Sending logout request to: {url}")

        response = self.session.post(
            url,
            headers=self._get_auth_headers(),
            timeout=timeout,
            verify=False 
        )

        if response.status_code == 200:
            print("Logout successful")
        else:
            print(f"Logout returned status {response.status_code}: {response.text}")

        return response

    def get_stations(self, timeout: int = 10) -> dict[str, Any]:
        """
        Get the list of available stations for the authenticated user.

        Endpoint from Swagger:
        GET /api/easywind_stations/station
        """
        url = f"{self.api_base_url}/easywind_stations/station"
        print(f"Requesting station list from: {url}")

        response = self.session.get(
            url,
            headers=self._get_auth_headers(),
            timeout=timeout,
        )

        response.raise_for_status()
        print("Station list retrieved successfully.")

        return response.json()

    def get_station_measurements(
        self,
        station_id: str,
        *,
        date: Optional[str] = None,
        output: str = "json",
        data: Optional[str] = None,
        period: Optional[str] = None,
        last_seconds: Optional[str] = None,
        interval: Optional[str] = None,
        window_size: Optional[str] = None,
        limit: Optional[str] = None,
        init: Optional[str] = None,
        end: Optional[str] = None,
        filename: Optional[str] = None,
        json_type: Optional[str] = None,
        timeout: int = 20,
    ) -> Any:
        """
        Get historical measurements for one station.

        Endpoint from Swagger:
        GET /api/easywind_data_operations/{station_id}/getmeasurements

        Only provided parameters are sent.
        """
        url = f"{self.api_base_url}/easywind_data_operations/{station_id}/getmeasurements"

        params = {
            "date": date,
            "output": output,
            "data": data,
            "period": period,
            "last_seconds": last_seconds,
            "interval": interval,
            "window_size": window_size,
            "limit": limit,
            "init": init,
            "end": end,
            "filename": filename,
            "json_type": json_type,
        }

        # Remove keys with None values so the request stays clean
        params = {key: value for key, value in params.items() if value is not None}

        print(f"Requesting measurements for station: {station_id}")
        print(f"GET {url}")
        print(f"Query params: {params}")

        response = self.session.get(
            url,
            headers=self._get_auth_headers(),
            params=params,
            timeout=timeout,
        )

        response.raise_for_status()

        # If output is JSON, parse it. Otherwise return raw text/content.
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            print("Measurements retrieved as JSON.")
            return response.json()

        print("Measurements retrieved as non-JSON response.")
        return response.text

    # ------------------------------------------------------------------
    # Public Socket.IO methods
    # ------------------------------------------------------------------

    def set_stream_handler(self, callback: Callable[[Any], None]) -> None:
        """
        Replace the default 'stream_data' event handler.

        Parameters
        ----------
        callback : callable
            Function that receives the event payload
        """
        self.sio.on("stream_data", callback)

    def connect_socket(self, wait_timeout: int = 10) -> None:
        """
        Connect to the Socket.IO server.

        The Socket.IO server uses the base URL, not /api.
        Example:
            https://server.example.com
        """
        headers: dict[str, str] = {}

        if self.mac:
            headers["MAC"] = self.mac

        print(f"Connecting to Socket.IO endpoint at: {self.base_url}")

        self.sio.connect(
            self.base_url,
            headers=headers,
            transports=["websocket", "polling"],
            wait_timeout=wait_timeout,
        )

    def wait_forever(self) -> None:
        """
        Block the process and keep listening for events.
        """
        print("Listening for real-time events...")
        self.sio.wait()

    def disconnect_socket(self) -> None:
        """
        Disconnect from Socket.IO if currently connected.
        """
        if self.sio.connected:
            print("Disconnecting from Socket.IO...")
            self.sio.disconnect()# coding: utf-8

"""
Windalytics external client.

This client supports:
1. Login through the REST API
2. Token storage
3. Real-time Socket.IO connection
4. Optional authenticated REST requests

Designed for external customers who need a simple integration example.
"""

import json
import logging
from typing import Any, Callable, Optional

import requests
import socketio


class WindalyticsClient:
    """
    Client for the Windalytics platform.

    Parameters
    ----------
    base_url : str
        Server base URL, for example:
        http://127.0.0.1:5000
        https://api.example.com

    token : str | None
        Existing access token. Optional if you will call login() first.

    mac : str | None
        Optional MAC header sent during Socket.IO connection.
        Your backend reads this header on connect, but it is not required
        for standard viewer/external clients.

    log_level : str
        Logging level: DEBUG, INFO, WARNING, ERROR
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        mac: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_base_url = f"{self.base_url}/api"
        self.token = token
        self.mac = mac

        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)s | %(message)s",
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # requests session for REST API calls
        self.session = requests.Session()

        # Socket.IO client for real-time streaming
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,   # infinite retries
            reconnection_delay=2,
            reconnection_delay_max=15,
        )

        self._register_default_socket_events()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_default_socket_events(self) -> None:
        """
        Register default Socket.IO event handlers.

        External users can replace the 'stream_data' handler later with
        set_stream_handler().
        """

        @self.sio.event
        def connect() -> None:
            print(f"Connected to Socket.IO server: {self.base_url}")

            if not self.token:
                print("No token available. Please call login() first or provide a token.")
                return

            # Your backend expects the token as payload of the 'join' event.
            print("Sending join request with access token...")
            self.sio.emit("join", self.token)

        @self.sio.event
        def disconnect() -> None:
            print("Disconnected from Socket.IO server")

        @self.sio.event
        def connect_error(data: Any) -> None:
            print("Socket.IO connection error:", data)

        @self.sio.on("stream_data")
        def stream_data(payload: Any) -> None:
            """
            Default event handler for real-time data.

            This can be overridden with set_stream_handler().
            """
            print("Received stream_data event:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Build Authorization header for protected REST endpoints.

        Swagger defines Bearer Auth in the Authorization header.
        """
        if not self.token:
            raise RuntimeError("No token available. Please login first.")

        return {
            "Authorization": f"{self.token}"
        }

    def _extract_token_from_login_response(self, data: dict[str, Any]) -> str:
        """
        Try to extract the token from different possible response formats.

        Because Swagger does not define the exact login response schema,
        we support several common patterns.
        """
        possible_paths = [
            data.get("Authorization"),
            data.get("access_token"),
            data.get("auth_token"),
            data.get("jwt"),
            data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None,
            data.get("response", {}).get("token") if isinstance(data.get("response"), dict) else None,
        ]

        token = next((value for value in possible_paths if value), None)

        if not token:
            raise ValueError(
                "Could not find token in login response. "
                f"Received response: {data}"
            )

        return token

    # ------------------------------------------------------------------
    # Public REST API methods
    # ------------------------------------------------------------------

    def login(self, email: str, password: str, timeout: int = 10) -> str:
        """
        Authenticate against the REST API and store the token.

        Endpoint from Swagger:
        POST /api/auth/login/

        Parameters
        ----------
        email : str
            User email
        password : str
            User password
        timeout : int
            Request timeout in seconds

        Returns
        -------
        str
            Access token
        """
        url = f"{self.api_base_url}/auth/login/"
        payload = {
            "email": email,
            "password": password,
        }
        print(f"Attempting to login with email: {email}")
        print(f"Requesting token from: {url}")

        response = self.session.post(url, json=payload, timeout=timeout, verify=False )

        if response.status_code != 200:
            raise RuntimeError(
                f"Login failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        token = self._extract_token_from_login_response(data)

        self.token = token
        print("Login successful. Token received and stored.")

        return token

    def logout(self, timeout: int = 10) -> requests.Response:
        """
        Logout through the REST API.

        Endpoint from Swagger:
        POST /api/auth/logout/
        """
        url = f"{self.api_base_url}/auth/logout/"
        print(f"Sending logout request to: {url}")

        response = self.session.post(
            url,
            headers=self._get_auth_headers(),
            timeout=timeout,
            verify=False 
        )

        if response.status_code == 200:
            print("Logout successful")
        else:
            print(f"Logout returned status {response.status_code}: {response.text}")

        return response

    def get_stations(self, timeout: int = 10) -> dict[str, Any]:
        """
        Get the list of available stations for the authenticated user.

        Endpoint from Swagger:
        GET /api/easywind_stations/station
        """
        url = f"{self.api_base_url}/easywind_stations/station"
        print(f"Requesting station list from: {url}")

        response = self.session.get(
            url,
            headers=self._get_auth_headers(),
            timeout=timeout,
            verify=False
        )

        response.raise_for_status()
        print("Station list retrieved successfully.")

        return response.json()

    def get_station_measurements(
        self,
        station_id: str,
        *,
        date: Optional[str] = None,
        output: str = "json",
        data: Optional[str] = None,
        period: Optional[str] = None,
        last_seconds: Optional[str] = None,
        interval: Optional[str] = None,
        window_size: Optional[str] = None,
        limit: Optional[str] = None,
        init: Optional[str] = None,
        end: Optional[str] = None,
        filename: Optional[str] = None,
        json_type: Optional[str] = None,
        timeout: int = 20,
    ) -> Any:
        """
        Get historical measurements for one station.

        Endpoint from Swagger:
        GET /api/easywind_data_operations/{station_id}/getmeasurements

        Only provided parameters are sent.
        """
        url = f"{self.api_base_url}/easywind_data_operations/{station_id}/getmeasurements"

        params = {
            "date": date,
            "output": output,
            "data": data,
            "period": period,
            "last_seconds": last_seconds,
            "interval": interval,
            "window_size": window_size,
            "limit": limit,
            "init": init,
            "end": end,
            "filename": filename,
            "json_type": json_type,
        }

        # Remove keys with None values so the request stays clean
        params = {key: value for key, value in params.items() if value is not None}

        print(f"Requesting measurements for station: {station_id}")
        print(f"GET {url}")
        print(f"Query params: {params}")

        response = self.session.get(
            url,
            headers=self._get_auth_headers(),
            params=params,
            timeout=timeout,
            verify=False
        )

        response.raise_for_status()

        # If output is JSON, parse it. Otherwise return raw text/content.
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            print("Measurements retrieved as JSON.")
            return response.json()

        print("Measurements retrieved as non-JSON response.")
        return response.text

    # ------------------------------------------------------------------
    # Public Socket.IO methods
    # ------------------------------------------------------------------

    def set_stream_handler(self, callback: Callable[[Any], None]) -> None:
        """
        Replace the default 'stream_data' event handler.

        Parameters
        ----------
        callback : callable
            Function that receives the event payload
        """
        self.sio.on("stream_data", callback)

    def connect_socket(self, wait_timeout: int = 10) -> None:
        """
        Connect to the Socket.IO server.

        The Socket.IO server uses the base URL, not /api.
        Example:
            https://server.example.com
        """
        headers: dict[str, str] = {}

        if self.mac:
            headers["MAC"] = self.mac

        print(f"Connecting to Socket.IO endpoint at: {self.base_url}")

        self.sio.connect(
            self.base_url,
            headers=headers,
            transports=["websocket", "polling"],
            wait_timeout=wait_timeout,
        )

    def wait_forever(self) -> None:
        """
        Block the process and keep listening for events.
        """
        print("Listening for real-time events...")
        self.sio.wait()

    def disconnect_socket(self) -> None:
        """
        Disconnect from Socket.IO if currently connected.
        """
        if self.sio.connected:
            print("Disconnecting from Socket.IO...")
            self.sio.disconnect()