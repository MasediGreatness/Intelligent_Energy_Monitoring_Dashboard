"""Command-line entry point for seed and scenario generation."""

import argparse
import json
from datetime import datetime

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.simulator.generator import Scenario, generate_simulation
from app.simulator.persistence import persist_simulation, seed_devices


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Deterministic energy simulator")
    subcommands = command.add_subparsers(dest="command", required=True)
    subcommands.add_parser("seed", help="Upsert the five demonstration devices")
    generate = subcommands.add_parser(
        "generate", help="Generate a deterministic scenario"
    )
    generate.add_argument(
        "--start", required=True, help="Timezone-aware ISO 8601 timestamp"
    )
    generate.add_argument("--seconds", type=int, default=60)
    generate.add_argument(
        "--scenario",
        choices=[item.value for item in Scenario],
        default=Scenario.NORMAL.value,
    )
    generate.add_argument("--persist", action="store_true")
    return command


def main() -> None:
    args = parser().parse_args()
    with get_session_factory()() as session:
        if args.command == "seed":
            print(json.dumps({"devices_seeded": seed_devices(session)}))
            return
        result = generate_simulation(
            datetime.fromisoformat(args.start.replace("Z", "+00:00")),
            args.seconds,
            get_settings().SIMULATOR_SEED,
            Scenario(args.scenario),
        )
        summary = {
            "scenario": args.scenario,
            "measurements": len(result.measurements),
            "forecasts": len(result.forecasts),
            "anomalies": len(result.anomalies),
            "events": len(result.events),
        }
        if args.persist:
            seed_devices(session)
            summary.update(persist_simulation(session, result))
        print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
