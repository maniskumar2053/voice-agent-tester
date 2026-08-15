# Loom recording outlines

## 1. Project walkthrough (under 3 minutes, webcam on)

- **0:00–0:20 — Outcome:** play 10–15 seconds from the strongest call; state what the caller achieved.
- **0:20–0:50 — Architecture:** show `ARCHITECTURE.md`; explain PSTN → Twilio → WebSocket bridge → Realtime.
- **0:50–1:25 — Conversation quality:** show scenario prompt, VAD, interruption truncation, and codec passthrough.
- **1:25–1:55 — Evidence:** open one synchronized transcript/MP3 and its verified bug entry.
- **1:55–2:25 — Iteration:** compare an early awkward call with a later improved call and name the exact change.
- **2:25–2:50 — Judgment:** explain direct bridge vs framework and automated triage vs human verification.
- **2:50–3:00 — Close:** show tests and the one-command suite invocation.

## 2. AI-assisted debugging (separate public recording, webcam on)

Record a real debugging session; do not stage a fake defect. Show the prompt, test failure or call symptom,
the proposed patch, your review, and the verification run. Useful prompt shape:

> The remote party began speaking at media timestamp X, but our caller audio continued for Y ms. Inspect
> these event lines and the bridge code. Identify the protocol-level cause, propose the smallest patch,
> and add a regression test. Do not change unrelated code.

Explain where you rejected or refined the AI's suggestion. Hide `.env`, tokens, account identifiers, and
patient-like test data before recording.

