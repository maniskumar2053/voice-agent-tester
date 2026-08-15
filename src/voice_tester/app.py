from __future__ import annotations

import asyncio
import json

import websockets
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Connect, VoiceResponse

from .artifacts import CallArtifacts
from .config import Settings
from .scenarios import get_scenario


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings()  # type: ignore[call-arg]
    app = FastAPI(title="Voice Agent Tester")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/twilio/voice")
    async def voice(request: Request) -> Response:
        form = await request.form()
        if not _valid_twilio_request(request, dict(form), cfg):
            return Response("invalid signature", status_code=403)
        scenario_id = request.query_params.get("scenario")
        if not scenario_id:
            return Response("missing scenario", status_code=400)
        get_scenario(scenario_id)
        response = VoiceResponse()
        connect = Connect()
        connect.stream(url=f"{cfg.public_ws_url}/media?scenario={scenario_id}")
        response.append(connect)
        return Response(str(response), media_type="application/xml")

    @app.websocket("/media")
    async def media(twilio_ws: WebSocket) -> None:
        await twilio_ws.accept()
        scenario_id = twilio_ws.query_params.get("scenario", "")
        scenario = get_scenario(scenario_id)
        realtime_url = f"wss://api.openai.com/v1/realtime?model={cfg.openai_realtime_model}"
        headers = {"Authorization": f"Bearer {cfg.openai_api_key}"}
        artifacts: CallArtifacts | None = None
        stream_sid: str | None = None
        latest_media_ms = 0
        response_start_ms: int | None = None
        current_item_id: str | None = None

        async with websockets.connect(realtime_url, additional_headers=headers) as openai_ws:
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": cfg.openai_realtime_model,
                    "instructions": scenario.prompt(),
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcmu"},
                            "transcription": {"model": "gpt-4o-mini-transcribe"},
                            "turn_detection": {
                                "type": "server_vad", "threshold": 0.5,
                                "prefix_padding_ms": 300, "silence_duration_ms": 550,
                            },
                        },
                        "output": {"format": {"type": "audio/pcmu"}, "voice": cfg.openai_voice},
                    },
                },
            }))

            async def from_twilio() -> None:
                nonlocal artifacts, stream_sid, latest_media_ms
                try:
                    async for raw in twilio_ws.iter_text():
                        message = json.loads(raw)
                        if message["event"] == "start":
                            stream_sid = message["start"]["streamSid"]
                            call_sid = message["start"]["callSid"]
                            artifacts = CallArtifacts(cfg.artifact_dir, call_sid, scenario)
                        elif message["event"] == "media":
                            latest_media_ms = int(message["media"]["timestamp"])
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": message["media"]["payload"],
                            }))
                        elif message["event"] == "stop":
                            if artifacts:
                                artifacts.write_metadata({"status": "stream-stopped"})
                            break
                except WebSocketDisconnect:
                    pass

            async def from_openai() -> None:
                nonlocal response_start_ms, current_item_id
                async for raw in openai_ws:
                    event = json.loads(raw)
                    if artifacts:
                        artifacts.event(event)
                    kind = event.get("type")
                    if kind == "response.output_audio.delta" and stream_sid:
                        if response_start_ms is None:
                            response_start_ms = latest_media_ms
                        current_item_id = event.get("item_id", current_item_id)
                        await twilio_ws.send_json({
                            "event": "media", "streamSid": stream_sid,
                            "media": {"payload": event["delta"]},
                        })
                    elif kind == "response.output_audio_transcript.done" and artifacts:
                        artifacts.turn("CALLER_BOT", event.get("transcript", ""))
                    elif kind == "conversation.item.input_audio_transcription.completed" and artifacts:
                        artifacts.turn("TEST_LINE_AGENT", event.get("transcript", ""))
                    elif kind == "input_audio_buffer.speech_started" and current_item_id and stream_sid:
                        elapsed = max(0, latest_media_ms - (response_start_ms or latest_media_ms))
                        await openai_ws.send(json.dumps({
                            "type": "conversation.item.truncate", "item_id": current_item_id,
                            "content_index": 0, "audio_end_ms": elapsed,
                        }))
                        await twilio_ws.send_json({"event": "clear", "streamSid": stream_sid})
                        response_start_ms = None
                        current_item_id = None
                    elif kind == "error":
                        if artifacts:
                            artifacts.write_metadata({"status": "realtime-error", "error": event.get("error")})

            tasks = [asyncio.create_task(from_twilio()), asyncio.create_task(from_openai())]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*done, *pending, return_exceptions=True)
        if artifacts:
            artifacts.write_metadata({"status": "completed"})

    return app


def _valid_twilio_request(request: Request, form: dict[str, object], settings: Settings) -> bool:
    signature = request.headers.get("X-Twilio-Signature", "")
    url = settings.public_base_url + request.url.path
    if request.url.query:
        url += "?" + request.url.query
    return RequestValidator(settings.twilio_auth_token).validate(url, form, signature)


app = create_app()
