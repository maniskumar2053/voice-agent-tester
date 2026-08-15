# Voice Agent Tester

An automated, goal-driven “patient” that calls only the Pretty Good AI assessment line, holds a natural
voice conversation, records and transcribes both sides, and triages possible quality issues.

> **Status:** the code and scenarios are ready, but this repository intentionally includes no invented
> call evidence. You must run at least 10 real calls, listen to them, and commit the MP3s, transcripts,
> and verified report before submitting.

## How it works

Twilio makes the call and streams phone audio to this server. The bridge connects server-to-server to
OpenAI Realtime, which acts as the patient and supports conversational turn-taking. Audio stays in
G.711 μ-law end to end. Twilio records the call; Realtime transcript events provide labeled turns.

## Setup

Prerequisites: Python 3.11+, a Twilio number capable of US outbound calls, an OpenAI API key, and a
public HTTPS tunnel or deployment. Follow recording-consent laws applicable to your originating and
destination jurisdictions.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill `.env`. Do not change `TEST_PHONE_NUMBER`; startup rejects any value except `+18054398008`.
Expose local port 8000 with your preferred HTTPS tunnel and set `PUBLIC_BASE_URL` to that URL.

```bash
uvicorn voice_tester.app:app --host 0.0.0.0 --port 8000
```

In another terminal, confirm health, list scenarios, and make one calibration call:

```bash
curl https://YOUR_PUBLIC_HOST/health
voice-tester list
voice-tester call 01-schedule --confirm-number +18054398008
```

Listen to the first call before running a suite. Tune pacing/VAD if necessary, then run 10 diverse calls:

```bash
voice-tester suite --count 10 --confirm-number +18054398008
```

These are real, billable calls. The typed confirmation plus hard-coded allowlist is intentional.

## Evidence workflow

Call folders appear under `artifacts/calls/<scenario>_<CallSid>/` with `transcript.txt`, `events.jsonl`,
and `metadata.json`. Download only recordings made by the configured source number to the locked test line:

```bash
voice-tester download
```

Analyze each transcript, aggregate candidate findings, then verify every finding by listening to audio:

```bash
voice-tester analyze artifacts/calls/01-schedule_CA.../transcript.txt
voice-tester report
```

Before submission, put each matching MP3 inside its call folder (or clearly map recordings in the report),
ensure there are at least 10 full conversations, and remove recordings that contain unintended sensitive
data. Do not rely on automated analysis alone.

## Quality checklist

- Caller waits for the greeting and uses short, natural turns.
- Caller repairs misunderstandings and steers back to the scenario outcome.
- Interruptions stop playback quickly; no long double-talk or dead air.
- Transcript labels match the recording and final confirmation.
- Bugs are material, reproducible, timestamped, and supported by exact evidence.
- All calls originate from the single number reported on the submission form.
- Repository is public; both webcam-on Loom videos are public; no secrets are committed.

## Commands

- `voice-tester list` — show 12 scenarios.
- `voice-tester call ID --confirm-number +18054398008` — one real call.
- `voice-tester suite --count 10 --confirm-number +18054398008` — sequential suite.
- `voice-tester download` — fetch matching Twilio recordings as MP3.
- `voice-tester analyze TRANSCRIPT` — create structured candidate findings.
- `voice-tester report` — compile analyses into `artifacts/BUG_REPORT.md`.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design tradeoffs and [LOOM_SCRIPT.md](LOOM_SCRIPT.md) for the
two required recordings.
