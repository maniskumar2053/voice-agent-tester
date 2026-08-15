# Architecture

Twilio owns the PSTN edge: it originates each call from one configured number, records both sides,
and sends 8 kHz μ-law media frames to a FastAPI WebSocket. The service bridges those frames to the
OpenAI Realtime API using the same codec, avoiding a resampling step and its latency/artifacts.
Realtime server VAD controls turn boundaries; when the remote agent interrupts, the bridge truncates
the current model item and clears Twilio's playback buffer so the simulated patient stops speaking.
Completed input and output transcript events are labeled by speaker and written incrementally, while
Twilio's recording remains the audio source of truth.

I chose a direct bridge over a heavier voice framework because the assessment has one fixed route and
values inspectability. Scenario prompts encode goals and facts but let the model choose wording and
repairs, producing a realistic caller rather than a prerecorded script. A second model reviews each
transcript into structured issue records, but the README explicitly requires human verification
against the recording before submission. Safety is enforced in code and configuration: the destination
is a constant allowlist, real calls need the number typed again, credentials stay in `.env`, and
recording downloads filter both destination and originating number.

