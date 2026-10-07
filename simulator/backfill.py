"""One-shot backfill: generate historical readings for the last N hours.

Useful for a freshly-deployed demo DB that has no data yet.

    python -m simulator.backfill --hours 24 --interval 60

Writes readings with timestamps spread over the past 24 hours, so charts
on a first-time visit are not empty.

Run against production:
    BACKEND_URL=https://your-service.onrender.com python -m simulator.backfill --hours 24
"""
import argparse
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from simulator.client import BackendClient
from simulator.config import settings
from simulator.generator import generate_reading
from simulator.logging_config import configure_logging

configure_logging(settings.simulator_log_level)
logger = logging.getLogger("backfill")

SensorPlanEntry = Tuple[int, str, Dict[str, Tuple[float, float]]]

DEFAULT_TARGETS = {
    "temperature": (18.0, 26.0),
    "humidity": (60.0, 80.0),
    "soil_moisture": (55.0, 75.0),
}

BATCH_SIZE = 500  # readings per POST


def _targets_for_zone(zone: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    def pick(prefix: str) -> Tuple[float, float]:
        lo = zone.get(f"target_{prefix}_min")
        hi = zone.get(f"target_{prefix}_max")
        if lo is None or hi is None:
            return DEFAULT_TARGETS[prefix]
        return (float(lo), float(hi))
    return {
        "temperature": pick("temperature"),
        "humidity": pick("humidity"),
        "soil_moisture": pick("soil_moisture"),
    }


def build_sensor_plan(topology: List[Dict[str, Any]]) -> List[SensorPlanEntry]:
    plan: List[SensorPlanEntry] = []
    for gh in topology:
        for zone in gh["zones"]:
            targets = _targets_for_zone(zone)
            for s in zone["sensors"]:
                plan.append((s["id"], s["sensor_type"], targets))
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill historical sensor readings.")
    parser.add_argument("--hours", type=int, default=24, help="Hours of history to generate.")
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Seconds between readings (60 = one per minute per sensor).",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    client = BackendClient(settings.backend_url, timeout=60.0)
    try:
        topology = client.get_topology()
        if not topology:
            raise RuntimeError("Empty topology. Run the seed first.")
        plan = build_sensor_plan(topology)
        logger.info("Loaded %d sensors", len(plan))

        rng = random.Random(args.seed)
        state: Dict[int, Dict[str, float]] = {}

        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = now - timedelta(hours=args.hours)
        total_points = (args.hours * 3600) // args.interval

        all_readings: List[Dict[str, Any]] = []
        for i in range(total_points):
            ts = start + timedelta(seconds=i * args.interval)
            for sensor_id, sensor_type, targets in plan:
                s_state = state.setdefault(sensor_id, {})
                value = generate_reading(
                    sensor_type=sensor_type,
                    targets=targets,
                    now=ts,
                    sensor_state=s_state,
                    rng=rng,
                    anomaly_probability=settings.simulator_anomaly_probability,
                )
                all_readings.append({
                    "sensor_id": sensor_id,
                    "timestamp": ts.isoformat(),
                    "value": value,
                })

        logger.info(
            "Generated %d readings across %d timestamps; posting in batches of %d",
            len(all_readings), total_points, BATCH_SIZE,
        )

        inserted = 0
        rejected = 0
        duplicates = 0
        t0 = time.monotonic()
        for i in range(0, len(all_readings), BATCH_SIZE):
            batch = all_readings[i : i + BATCH_SIZE]
            stats = client.post_readings(batch)
            inserted += stats.get("inserted", 0)
            rejected += stats.get("rejected", 0)
            duplicates += stats.get("duplicates", 0)
            logger.info(
                "Batch %d/%d: inserted=%d rejected=%d duplicates=%d",
                i // BATCH_SIZE + 1,
                (len(all_readings) + BATCH_SIZE - 1) // BATCH_SIZE,
                stats.get("inserted", 0),
                stats.get("rejected", 0),
                stats.get("duplicates", 0),
            )

        elapsed = time.monotonic() - t0
        logger.info(
            "Done. inserted=%d rejected=%d duplicates=%d in %.1fs",
            inserted, rejected, duplicates, elapsed,
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()