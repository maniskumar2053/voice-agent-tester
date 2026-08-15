from __future__ import annotations

from pathlib import Path

import httpx
from twilio.rest import Client

from .config import ASSESSMENT_NUMBER, Settings


def place_call(settings: Settings, scenario_id: str) -> str:
    if settings.test_phone_number != ASSESSMENT_NUMBER:
        raise ValueError("refusing call: destination allowlist violation")
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=ASSESSMENT_NUMBER,
        from_=settings.twilio_from_number,
        url=f"{settings.public_base_url}/twilio/voice?scenario={scenario_id}",
        method="POST",
        record=True,
        recording_channels="dual",
        timeout=30,
    )
    return call.sid


def download_recordings(settings: Settings) -> list[Path]:
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    root = settings.artifact_dir / "recordings"
    root.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    with httpx.Client(auth=(settings.twilio_account_sid, settings.twilio_auth_token), timeout=60) as http:
        for recording in client.recordings.list(limit=100):
            call = client.calls(recording.call_sid).fetch()
            if call.to != ASSESSMENT_NUMBER or call.from_ != settings.twilio_from_number:
                continue
            target = root / f"{recording.call_sid}.mp3"
            response = http.get(f"https://api.twilio.com{recording.uri.removesuffix('.json')}.mp3")
            response.raise_for_status()
            target.write_bytes(response.content)
            saved.append(target)
    return saved
