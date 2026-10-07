import logging
import random
import signal
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from simulator.client import BackendClient
from simulator.config import settings
from simulator.generator import generate_reading
from simulator.logging_config import configure_logging

configure_logging(settings.simulator_log_level)
logger = logging.getLogger("simulator")

SensorPlanEntry = Tuple[int, str, Dict[str, Tuple[float, float]]]

# Fallback targets used if the topology payload does not carry per-zone targets.
# Values match the tomato defaults seeded in Phase 2.
DEFAULT_TARGETS: Dict[str, Tuple[float, float]] = {
    "temperature": (18.0, 26.0),
    "humidity": (60.0, 80.0),
    "soil_moisture": (55.0, 75.0),
}


def _targets_for_zone(zone: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    """Return (min, max) targets for a zone.

    Prefers values from the topology payload. If any pair is missing, logs a
    warning and falls back to DEFAULT_TARGETS for that metric so the simulator
    can still run against older/leaner backends.
    """

    def pick(prefix: str) -> Tuple[float, float]:
        lo = zone.get(f"target_{prefix}_min")
        hi = zone.get(f"target_{prefix}_max")
        if lo is None or hi is None:
            logger.warning(
                "Zone %s missing target_%s_*; using defaults %s",
                zone.get("id"), prefix, DEFAULT_TARGETS[prefix],
            )
            return DEFAULT_TARGETS[prefix]
        return (float(lo), float(hi))

    return {
        "temperature": pick("temperature"),
        "humidity": pick("humidity"),
        "soil_moisture": pick("soil_moisture"),
    }


def build_sensor_plan(topology: List[Dict[str, Any]]) -> List[SensorPlanEntry]:
    """Flatten the greenhouse -> zone -> sensor hierarchy into a sensor plan.

    Each entry is (sensor_id, sensor_type, targets) where targets is the
    dict of (min, max) pairs for that zone.
    """
    plan: List[SensorPlanEntry] = []
    for gh in topology:
        for zone in gh["zones"]:
            targets = _targets_for_zone(zone)
            for s in zone["sensors"]:
                plan.append((s["id"], s["sensor_type"], targets))
    return plan


def fetch_topology_with_retry(client: BackendClient) -> List[Dict[str, Any]]:
    """Retry fetching /topology until the backend is reachable and returns data."""
    for attempt in range(1, settings.simulator_topology_max_retries + 1):
        try:
            topology = client.get_topology()
            if topology:
                logger.info("Fetched topology: %d greenhouses", len(topology))
                return topology
            logger.warning("Topology empty, retrying...")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Topology fetch failed (attempt %d): %s", attempt, exc)
        time.sleep(settings.simulator_topology_retry_seconds)
    raise RuntimeError("Could not fetch topology after retries")


def run_cycle(
    client: BackendClient,
    plan: List[SensorPlanEntry],
    state: Dict[int, Dict[str, float]],
    rng: random.Random,
) -> Dict[str, int]:
    """Generate one reading per sensor and POST the batch to the backend."""
    now = datetime.now(timezone.utc)
    readings = []
    for sensor_id, sensor_type, targets in plan:
        sensor_state = state.setdefault(sensor_id, {})
        value = generate_reading(
            sensor_type=sensor_type,
            targets=targets,
            now=now,
            sensor_state=sensor_state,
            rng=rng,
            anomaly_probability=settings.simulator_anomaly_probability,
        )
        readings.append(
            {
                "sensor_id": sensor_id,
                "timestamp": now.isoformat(),
                "value": value,
            }
        )
    logger.info("Generated %d sensor readings", len(readings))
    stats = client.post_readings(readings)
    logger.info(
        "Successfully ingested %d readings (rejected=%d duplicates=%d)",
        stats["inserted"], stats["rejected"], stats["duplicates"],
    )
    return stats


def main() -> None:
    client = BackendClient(
        settings.backend_url, timeout=settings.simulator_request_timeout
    )
    shutdown = {"flag": False}

    def handle_signal(signum, _frame):
        logger.info("Shutdown signal received (%s)", signum)
        shutdown["flag"] = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        topology = fetch_topology_with_retry(client)
        plan = build_sensor_plan(topology)
        logger.info(
            "Loaded %d sensors across %d greenhouses",
            len(plan), len(topology),
        )

        rng = random.Random()
        state: Dict[int, Dict[str, float]] = {}

        while not shutdown["flag"]:
            start = time.monotonic()
            try:
                run_cycle(client, plan, state, rng)
            except Exception:  # noqa: BLE001
                logger.exception("Cycle failed; will retry on next tick")
            elapsed = time.monotonic() - start
            to_sleep = max(0.0, settings.simulator_interval_seconds - elapsed)
            end = time.monotonic() + to_sleep
            # Sleep in small increments so shutdown signals are handled promptly.
            while not shutdown["flag"] and time.monotonic() < end:
                time.sleep(min(0.25, end - time.monotonic()))
    finally:
        client.close()
        logger.info("Simulator stopped")


if __name__ == "__main__":
    main()