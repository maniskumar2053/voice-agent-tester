from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scenarios import Scenario


class CallArtifacts:
    def __init__(self, root: Path, call_sid: str, scenario: Scenario) -> None:
        self.directory = root / "calls" / f"{scenario.id}_{call_sid}"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.events_path = self.directory / "events.jsonl"
        self.transcript_path = self.directory / "transcript.txt"
        self.metadata_path = self.directory / "metadata.json"
        self.turns: list[dict[str, Any]] = []
        self.write_metadata({"call_sid": call_sid, "scenario": asdict(scenario), "status": "started"})

    def write_metadata(self, patch: dict[str, Any]) -> None:
        current: dict[str, Any] = {}
        if self.metadata_path.exists():
            current = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        current.update(patch)
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.metadata_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def event(self, payload: dict[str, Any]) -> None:
        safe = {k: v for k, v in payload.items() if k not in {"audio", "delta"}}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, ensure_ascii=False) + "\n")

    def turn(self, speaker: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        stamp = datetime.now(timezone.utc).isoformat()
        self.turns.append({"timestamp": stamp, "speaker": speaker, "text": text})
        with self.transcript_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {speaker}: {text}\n")

