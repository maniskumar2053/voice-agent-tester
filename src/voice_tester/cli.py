from __future__ import annotations

import argparse
import time
from pathlib import Path

from .analyze import analyze_transcript, build_bug_report
from .calls import download_recordings, place_call
from .config import Settings
from .scenarios import SCENARIOS, get_scenario


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="voice-tester")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list built-in scenarios")
    run = commands.add_parser("call", help="place one real, billable call")
    run.add_argument("scenario", choices=[s.id for s in SCENARIOS])
    run.add_argument("--confirm-number", required=True, help="must equal the assessment number")
    suite = commands.add_parser("suite", help="place the first N calls sequentially")
    suite.add_argument("--count", type=int, default=10, choices=range(1, 13))
    suite.add_argument("--confirm-number", required=True)
    suite.add_argument("--pause", type=int, default=10)
    commands.add_parser("download", help="download this caller number's recordings as MP3")
    analyze = commands.add_parser("analyze", help="analyze one transcript")
    analyze.add_argument("transcript", type=Path)
    commands.add_parser("report", help="combine analyses into BUG_REPORT.md")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "list":
        for scenario in SCENARIOS:
            print(f"{scenario.id}: {scenario.title}")
        return
    settings = Settings()  # type: ignore[call-arg]
    if args.command in {"call", "suite"} and args.confirm_number != settings.test_phone_number:
        raise SystemExit("Confirmation number does not match the locked assessment number; no call made.")
    if args.command == "call":
        scenario = get_scenario(args.scenario)
        print(f"Started {scenario.id}: {place_call(settings, scenario.id)}")
    elif args.command == "suite":
        for index, scenario in enumerate(SCENARIOS[: args.count]):
            print(f"Started {scenario.id}: {place_call(settings, scenario.id)}")
            if index + 1 < args.count:
                time.sleep(args.pause)
    elif args.command == "download":
        for path in download_recordings(settings):
            print(path)
    elif args.command == "analyze":
        print(analyze_transcript(settings, args.transcript))
    elif args.command == "report":
        print(build_bug_report(settings.artifact_dir))


if __name__ == "__main__":
    main()

