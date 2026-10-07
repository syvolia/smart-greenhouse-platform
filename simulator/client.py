import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def get_topology(self) -> List[Dict[str, Any]]:
        r = self._client.get("/topology")
        r.raise_for_status()
        return r.json()

    def post_readings(self, readings: List[Dict[str, Any]]) -> Dict[str, int]:
        r = self._client.post(
            "/ingestion/sensor-readings", json={"readings": readings}
        )
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()