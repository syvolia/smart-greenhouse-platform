import os

import httpx

class BackendClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        headers = {}
        api_key = os.environ.get("SIMULATOR_API_KEY")
        if api_key:
            headers["X-API-Key"] = api_key
        self._client = httpx.Client(base_url=base_url, timeout=timeout, headers=headers)

    def get_topology(self):
        r = self._client.get("/topology")
        r.raise_for_status()
        return r.json()

    def post_readings(self, readings):
        r = self._client.post("/ingestion/sensor-readings", json={"readings": readings})
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()